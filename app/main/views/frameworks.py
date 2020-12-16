# coding: utf-8

from datetime import datetime, timedelta
from flask import abort, url_for
from flask_login import current_user
from dmapiclient import APIError
from dmutils.flask import timed_render_template as render_template
from dmutils.formats import DATETIME_FORMAT, dateformat
from ... import data_api_client
from ...main import main

BRIEF_RESPONSE_STATUSES = ['draft', 'submitted', 'pending-awarded', 'awarded']


@main.route('/frameworks/<framework_slug>', methods=['GET'])
def opportunities_dashboard(framework_slug):
    try:
        framework = data_api_client.get_framework(slug=framework_slug)['frameworks']
        supplier_framework = data_api_client.get_supplier_framework_info(
            supplier_id=current_user.supplier_id,
            framework_slug=framework['slug']
        )['frameworkInterest']
    except APIError as e:
        abort(e.status_code)
    if not (framework['framework'] == 'digital-outcomes-and-specialists' and supplier_framework['onFramework']):
        abort(404)
    opportunities = data_api_client.find_brief_responses(
        supplier_id=current_user.supplier_id,
        framework=framework_slug,
        status=",".join(BRIEF_RESPONSE_STATUSES),
        with_data=False,
    )['briefResponses']

    # Split into two tables by status
    drafts, completed = [], []
    two_weeks_ago = (datetime.now() - timedelta(days=14))

    for opportunity in opportunities:
        brief = opportunity.get('brief')
        applicationsClosedAt = brief.get("applicationsClosedAt")

        if opportunity['status'] == 'draft':
            opportunity_row = [
                {"text": brief.get('title')},
                {"text": dateformat(applicationsClosedAt), "attributes": {"data-closed": applicationsClosedAt}},
                {"text": "Draft"},
            ]

            # Show applications for live briefs and briefs that closed up to 2 weeks ago
            if opportunity['brief']['status'] == 'live':
                if opportunity.get("essentialRequirementsMet"):
                    opportunity_url = url_for(
                        '.check_brief_response_answers',
                        brief_id=opportunity.get("briefId"),
                        brief_response_id=opportunity.get("id")
                    )
                else:
                    opportunity_url = url_for('.start_brief_response', brief_id=opportunity.get("briefId"))
                opportunity_row.append(
                    {"html": f'<a class="govuk-link" href="{opportunity_url}">Complete your application</a>'}
                )
                drafts.append(opportunity_row)
            elif applicationsClosedAt > two_weeks_ago.strftime(DATETIME_FORMAT):
                opportunity_url = url_for(
                    "external.get_brief_by_id",
                    framework_family=(brief.get("framework")).get("family"),
                    brief_id=opportunity.get("briefId")
                )
                opportunity_row.append(
                    {"html": f'<a class="govuk-link" href="{ opportunity_url }">Applications closed</a>'}
                )
                drafts.append(opportunity_row)
        else:
            opportunity_url = url_for(
                ".check_brief_response_answers",
                brief_id=opportunity.get("briefId"),
                brief_response_id=opportunity.get("id")
            )
            opportunity_row = [
                {"html": f'<a class="govuk-link" href="{ opportunity_url }">{brief.get("title")}</a>'},
                {"text": dateformat(applicationsClosedAt), "attributes": {"data-closed": applicationsClosedAt}}
            ]

            status = brief.get("status")
            if status == "cancelled":
                opportunity_row.append({"text": "Opportunity cancelled"})
            elif status == "unsuccessful":
                opportunity_row.append({"text": "Not won"})
            elif status == "withdrawn":
                opportunity_row.append({"text": "Opportunity withdrawn"})
            elif status == "closed" or status == "live":
                opportunity_row.append({"text": "Submitted"})
            elif opportunity.get("status") == "awarded":
                opportunity_row.append({"text": "Won"})
            elif status == "awarded":
                opportunity_row.append({"text": "Not won"})

            completed.append(opportunity_row)

    return render_template(
        "frameworks/opportunities_dashboard.html",
        framework=framework,
        completed=completed,
        drafts=drafts,
    ), 200
