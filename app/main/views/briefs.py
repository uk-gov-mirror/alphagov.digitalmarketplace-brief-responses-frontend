# coding: utf-8
from __future__ import unicode_literals

from flask import abort, flash, redirect, request, url_for, current_app
from flask_login import current_user

from dmapiclient import HTTPError
from dmutils.flask import timed_render_template as render_template
from dmutils.forms.helpers import get_errors_from_wtform

from ..helpers.briefs import (
    get_brief,
    is_supplier_eligible_for_brief,
    send_brief_clarification_question
)
from ..helpers.frameworks import get_framework_and_lot
from ..helpers.briefs import is_legacy_brief_response
from ...main import main, public, content_loader
from ... import data_api_client
from ..forms.briefs import AskClarificationQuestionForm

PUBLISHED_BRIEF_STATUSES = ['live', 'closed', 'awarded', 'cancelled', 'unsuccessful', 'withdrawn']

APPLICATION_SUBMITTED_FIRST_MESSAGE = "Your application has been submitted."
APPLICATION_UPDATED_MESSAGE = "Your application has been updated."
CLARIFICATION_QUESTION_SENT_MESSAGE = "Your question has been sent. " \
                                      "The buyer will post your question and their answer on the ‘{brief[title]}’ page."


@main.route('/<int:brief_id>/question-and-answer-session', methods=['GET'])
def question_and_answer_session(brief_id):
    brief = get_brief(data_api_client, brief_id, allowed_statuses=['live'])

    if brief['clarificationQuestionsAreClosed']:
        abort(404)

    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief, clarification_question=True)

    return render_template(
        "briefs/question_and_answer_session.html",
        brief=brief,
    ), 200


@main.route('/<int:brief_id>/ask-a-question', methods=['GET', 'POST'])
def ask_brief_clarification_question(brief_id):
    brief = get_brief(data_api_client, brief_id, allowed_statuses=['live'])

    if brief['clarificationQuestionsAreClosed']:
        abort(404)

    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief, clarification_question=True)

    form = AskClarificationQuestionForm(brief)
    if form.validate_on_submit():
        send_brief_clarification_question(data_api_client, brief, form.clarification_question.data)
        flash(CLARIFICATION_QUESTION_SENT_MESSAGE.format(brief=brief))
        form_url = url_for('.ask_brief_clarification_question', brief_id=brief_id)
        flash('{}?submitted=true'.format(form_url), 'track-page-view')

    errors = get_errors_from_wtform(form)

    return render_template(
        "briefs/clarification_question.html",
        brief=brief,
        form=form,
        errors=errors,
    ), 200 if not errors else 400


@main.route('/<int:brief_id>/responses/start', methods=['GET', 'POST'])
def start_brief_response(brief_id):
    brief = get_brief(data_api_client, brief_id, allowed_statuses=['live'])

    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief)

    brief_response = data_api_client.find_brief_responses(
        brief_id=brief_id,
        supplier_id=current_user.supplier_id,
        status='draft,submitted'
    )['briefResponses']

    if brief_response and brief_response[0]['status'] == 'submitted':
        return redirect(
            url_for(".check_brief_response_answers", brief_id=brief_id, brief_response_id=brief_response[0]['id'])
        )

    if request.method == 'POST':
        if brief_response and brief_response[0]['status'] == 'draft':
            return redirect(
                url_for('.edit_brief_response', brief_id=brief_id, brief_response_id=brief_response[0]['id'])
            )
        else:
            brief_response = data_api_client.create_brief_response(
                brief_id,
                current_user.supplier_id,
                {},
                current_user.email_address,
            )['briefResponses']
            brief_response_id = brief_response['id']
            return redirect(url_for('.edit_brief_response', brief_id=brief_id, brief_response_id=brief_response_id))

    existing_draft_response = False
    if brief_response and brief_response[0]['status'] == 'draft':
        existing_draft_response = brief_response[0]

    return render_template(
        "briefs/start_brief_response.html",
        brief=brief,
        existing_draft_response=existing_draft_response
    )


@main.route('/<int:brief_id>/responses/<int:brief_response_id>', methods=['GET'])
@main.route(
    '/<int:brief_id>/responses/<int:brief_response_id>/<string:question_id>',
    methods=['GET', 'POST']
)
@main.route(
    '/<int:brief_id>/responses/<int:brief_response_id>/<string:question_id>/edit',
    methods=['GET', 'POST'],
    endpoint="edit_single_question"
)
def edit_brief_response(brief_id, brief_response_id, question_id=None):
    edit_single_question_flow = request.endpoint.endswith('.edit_single_question')

    brief = get_brief(data_api_client, brief_id, allowed_statuses=['live'])
    brief_response = data_api_client.get_brief_response(brief_response_id)['briefResponses']

    if brief_response['briefId'] != brief['id'] or brief_response['supplierId'] != current_user.supplier_id:
        abort(404)

    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief)

    framework, lot = get_framework_and_lot(
        data_api_client, brief['frameworkSlug'], brief['lotSlug'], allowed_statuses=['live', 'expired'])

    max_day_rate = None
    role = brief.get('specialistRole')
    if role:
        brief_service = data_api_client.find_services(
            supplier_id=current_user.supplier_id,
            framework=brief['frameworkSlug'],
            status="published",
            lot=brief["lotSlug"],
        )["services"][0]
        max_day_rate = brief_service.get(role + "PriceMax")

    content = content_loader.get_manifest(
        brief['frameworkSlug'], 'edit_brief_response'
    ).filter({'lot': lot['slug'], 'brief': brief, 'max_day_rate': max_day_rate})

    section = content.get_section(content.get_next_editable_section_id())
    if section is None or not section.editable:
        abort(404)

    # If a question in a brief is optional and is unanswered by the buyer, the brief will have the key but will have no
    # data. The question will be skipped in the brief response flow (see below). If a user attempts to access the
    # question by directly visiting the url, this check will return a 404. It has been created specifically for nice to
    # have requirements, and works because briefs and responses share the same key for this question/response.
    if question_id in brief.keys() and not brief[question_id]:
        abort(404)

    # If a question is to be skipped in the normal flow (due to the reason above), we update the next_question_id.
    next_question_id = section.get_next_question_id(question_id)
    if next_question_id in brief.keys() and not brief[next_question_id]:
        next_question_id = section.get_next_question_id(next_question_id)

    def redirect_to_next_page():
        return redirect(url_for(
            '.edit_brief_response',
            brief_id=brief_id,
            brief_response_id=brief_response_id,
            question_id=next_question_id
        ))

    # If no question_id in url then redirect to first question
    if question_id is None:
        return redirect_to_next_page()

    question = section.get_question(question_id)
    if question is None:
        abort(404)

    # Unformat brief response into data for form
    service_data = question.unformat_data(brief_response)

    status_code = 200
    errors = {}
    if request.method == 'POST':
        try:
            data_api_client.update_brief_response(
                brief_response_id,
                question.get_data(request.form),
                current_user.email_address,
                page_questions=[question.id]
            )

        except HTTPError as e:
            errors = question.get_error_messages(e.message)
            status_code = 400
            service_data = question.unformat_data(question.get_data(request.form))

        else:
            if next_question_id and not edit_single_question_flow:
                return redirect_to_next_page()
            else:
                if edit_single_question_flow:
                    flash(APPLICATION_UPDATED_MESSAGE)
                return redirect(
                    url_for('.check_brief_response_answers', brief_id=brief_id, brief_response_id=brief_response_id)
                )

    previous_question_id = section.get_previous_question_id(question_id)
    # Skip previous question if the brief has no nice to have requirements
    if previous_question_id in brief.keys() and not brief[previous_question_id]:
        previous_question_id = section.get_previous_question_id(previous_question_id)

    previous_question_url = None
    if previous_question_id:
        previous_question_url = url_for(
            '.edit_brief_response',
            brief_id=brief_id,
            brief_response_id=brief_response_id,
            question_id=previous_question_id
        )

    return render_template(
        "briefs/edit_brief_response_question.html",
        brief=brief,
        errors=errors,
        is_last_page=False if next_question_id else True,
        previous_question_url=previous_question_url,
        question=question,
        service_data=service_data
    ), status_code


@main.route('/<int:brief_id>/responses/<int:brief_response_id>/application', methods=['GET', 'POST'])
def check_brief_response_answers(brief_id, brief_response_id):
    brief = get_brief(
        data_api_client, brief_id, allowed_statuses=['live', 'closed', 'awarded', 'cancelled', 'unsuccessful']
    )
    brief_response = data_api_client.get_brief_response(brief_response_id)['briefResponses']
    if brief_response['briefId'] != brief['id'] or brief_response['supplierId'] != current_user.supplier_id:
        abort(404)

    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief)

    framework, lot = get_framework_and_lot(
        data_api_client, brief['frameworkSlug'], brief['lotSlug'], allowed_statuses=['live', 'expired'])

    if is_legacy_brief_response(brief_response):
        display_brief_response_manifest = 'legacy_display_brief_response'
    else:
        display_brief_response_manifest = 'display_brief_response'

    response_content = content_loader.get_manifest(
        framework['slug'], display_brief_response_manifest).filter({'lot': lot['slug'], 'brief': brief})
    for section in response_content:
        section.inject_brief_questions_into_boolean_list_question(brief)

    error_message = None
    if request.method == 'POST':
        if brief["status"] == "live":
            try:
                submit_response = data_api_client.submit_brief_response(
                    brief_response_id,
                    current_user.email_address
                )
                if submit_response['briefResponses'].get('status') == 'draft':
                    # DB returned 200 OK but failed to update for some reason
                    error_message = 'There was a problem submitting your application.'
            except HTTPError as e:
                if e.status_code != 400:
                    # Unexpected error
                    raise
                try:
                    if any(v == 'answer_required' for v in e.message.values()):
                        # Missing section
                        error_message = 'You need to complete all the sections before you can submit your application.'
                except (TypeError, AttributeError):
                    pass

                if error_message is None:
                    # Some other bad request
                    current_app.logger.error(e)
                    error_message = 'There was a problem submitting your application.'
        else:
            error_message = "This opportunity has already closed for applications."

        if not error_message:
            flash(APPLICATION_SUBMITTED_FIRST_MESSAGE)
            # To trigger the analytics Virtual Page View
            redirect_url = url_for('.application_submitted', brief_id=brief_id)
            flash('{}?result=success'.format(redirect_url), 'track-page-view')
            return redirect(redirect_url)
        else:
            flash(error_message, 'error')
            # fall through to re-display page, consuming the flash message in the process

    return render_template(
        "briefs/check_your_answers.html",
        brief=brief,
        brief_response=brief_response,
        response_content=response_content
    )


@main.route('/<int:brief_id>/responses/result')
def application_submitted(brief_id):
    brief = get_brief(data_api_client, brief_id, allowed_statuses=PUBLISHED_BRIEF_STATUSES)
    if not is_supplier_eligible_for_brief(data_api_client, current_user.supplier_id, brief):
        return _render_not_eligible_for_brief_error_page(brief)

    brief_response = data_api_client.find_brief_responses(
        brief_id=brief_id,
        supplier_id=current_user.supplier_id
    )['briefResponses']

    if len(brief_response) == 0:
        # No application
        return redirect(url_for(".start_brief_response", brief_id=brief_id))
    if 'essentialRequirementsMet' not in brief_response[0] or brief_response[0].get('status') == 'draft':
        # Incomplete or Legacy application
        return redirect(
            url_for(".check_brief_response_answers", brief_id=brief_id, brief_response_id=brief_response[0]['id'])
        )

    # Otherwise the application is valid
    brief_response = brief_response[0]
    framework, lot = get_framework_and_lot(
        data_api_client, brief['frameworkSlug'], brief['lotSlug'], allowed_statuses=['live', 'expired'])

    response_content = content_loader.get_manifest(
        framework['slug'], 'display_brief_response').filter({'lot': lot['slug'], 'brief': brief})
    for section in response_content:
        section.inject_brief_questions_into_boolean_list_question(brief)

    brief_content = content_loader.get_manifest(
        framework['slug'], 'edit_brief').filter({'lot': lot['slug']})
    brief_summary = brief_content.summary(brief)

    return render_template(
        'briefs/application_submitted.html',
        brief=brief,
        brief_summary=brief_summary,
        brief_response=brief_response,
        response_content=response_content
    )


@public.route('/<int:brief_id>')
def redirect_to_public_opportunity_page(brief_id):
    """
    The external URL for the public brief page is managed within the Buyer FE.
    There is an edge case where a supplier may try to manipulate the URL from their
    brief application flow to reach the public brief page, which never reaches the Buyer FE because of the
    '/suppliers/opportunities/...' prefix, which nginx routes to the Brief Responses FE (here!).

    This redirect replaces the 'suppliers' prefix with the correct framework name, which allows nginx to route
    to the Buyer FE as expected, avoiding a NotImplemented 500 error.
    """
    brief = get_brief(data_api_client, brief_id)
    return redirect(
        url_for('external.get_brief_by_id', framework_family=brief['framework']['family'], brief_id=brief_id)
    )


def _render_not_eligible_for_brief_error_page(brief, clarification_question=False):
    common_kwargs = {
        "supplier_id": current_user.supplier_id,
        "framework": brief['frameworkSlug'],
        "status": "published",
    }

    if data_api_client.find_services(**common_kwargs)["services"]:
        if data_api_client.find_services(**dict(common_kwargs, lot=brief["lotSlug"]))["services"]:
            # deduce that the problem is that the roles don't match.
            reason = data_reason_slug = "supplier-not-on-role"
        else:
            reason = data_reason_slug = "supplier-not-on-lot"
    else:
        reason = "supplier-not-on-framework"
        data_reason_slug = "supplier-not-on-{}".format(brief['frameworkSlug'])

    return render_template(
        "briefs/not_is_supplier_eligible_for_brief_error.html",
        clarification_question=clarification_question,
        framework_name=brief['frameworkName'],
        lot=brief['lotSlug'],
        reason=reason,
        data_reason_slug=data_reason_slug
    ), 403
