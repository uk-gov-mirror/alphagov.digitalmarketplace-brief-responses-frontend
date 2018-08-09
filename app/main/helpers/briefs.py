# -*- coding: utf-8 -*-

import six

from flask import abort, current_app, escape, url_for
from flask_login import current_user

from dmapiclient.audit import AuditTypes
from dmutils.email.dm_notify import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_web_url_from_stage
from dmutils.formats import dateformat


def get_brief(data_api_client, brief_id, allowed_statuses=None):
    if allowed_statuses is None:
        allowed_statuses = []

    brief = data_api_client.get_brief(brief_id)['briefs']

    if allowed_statuses and brief['status'] not in allowed_statuses:
        abort(404)

    return brief


def is_supplier_eligible_for_brief(data_api_client, supplier_id, brief):
    return data_api_client.is_supplier_eligible_for_brief(supplier_id, brief['id'])


def send_brief_clarification_question(data_api_client, brief, clarification_question):
    questions_url = (
        get_web_url_from_stage(current_app.config["DM_ENVIRONMENT"])
        + url_for('external.supplier_questions',
                  framework_slug=brief["framework"]['slug'],
                  lot_slug=brief["lotSlug"],
                  brief_id=brief["id"])
    )

    notify_client = DMNotifyClient(current_app.config['DM_NOTIFY_API_KEY'])

    # Email the question to brief owners
    for email_address in get_brief_user_emails(brief):
        try:
            notify_client.send_email(
                email_address,
                template_id=current_app.config['NOTIFY_TEMPLATES']['clarification_question'],
                personalisation={
                    "brief_title": brief['title'],
                    "brief_name": brief['title'],
                    "message": escape(clarification_question),
                    "publish_by_date": dateformat(brief['clarificationQuestionsPublishedBy']),
                    "questions_url": questions_url
                },
                reference="clarification-question-{}".format(hash_string(email_address))
            )
        except EmailError as e:
            current_app.logger.error(
                "Brief question email failed to send. error={error} supplier_id={supplier_id} brief_id={brief_id}",
                extra={'error': six.text_type(e), 'supplier_id': current_user.supplier_id, 'brief_id': brief['id']}
            )

            abort(503, "Clarification question email failed to send")

    data_api_client.create_audit_event(
        audit_type=AuditTypes.send_clarification_question,
        user=current_user.email_address,
        object_type="briefs",
        object_id=brief['id'],
        data={"question": clarification_question, "briefId": brief['id'], "supplierId": current_user.supplier_id})

    brief_url = (
        get_web_url_from_stage(current_app.config["DM_ENVIRONMENT"])
        + url_for('external.get_brief_by_id', framework_family=brief['framework']['family'], brief_id=brief['id'])
    )

    # Send the supplier a copy of the question
    try:
        notify_client.send_email(
            current_user.email_address,
            template_id=current_app.config["NOTIFY_TEMPLATES"]["clarification_question_confirmation"],
            personalisation={
                "brief_name": brief['title'],
                "message": escape(clarification_question),
                "brief_url": brief_url,
            },
            reference="clarification-question-confirmation-{}".format(hash_string(current_user.email_address))
        )
    except EmailError as e:
        current_app.logger.error(
            "Brief question supplier email failed to send. error={error} supplier_id={supplier_id} brief_id={brief_id}",
            extra={'error': six.text_type(e), 'supplier_id': current_user.supplier_id, 'brief_id': brief['id']}
        )


def get_brief_user_emails(brief):
    return [user['emailAddress'] for user in brief['users'] if user['active']]
