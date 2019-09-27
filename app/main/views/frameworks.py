# coding: utf-8

from datetime import datetime, timedelta
from flask import abort
from flask_login import current_user
from dmapiclient import APIError
from dmutils.flask import timed_render_template as render_template
from dmutils.formats import DATETIME_FORMAT
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
        if opportunity['status'] == 'draft':
            # Show applications for live briefs and briefs that closed up to 2 weeks ago
            if opportunity['brief']['status'] == 'live':
                drafts.append(opportunity)
            elif opportunity['brief']['applicationsClosedAt'] > two_weeks_ago.strftime(DATETIME_FORMAT):
                drafts.append(opportunity)
        else:
            completed.append(opportunity)

    return render_template(
        "frameworks/opportunities_dashboard.html",
        framework=framework,
        completed=completed,
        drafts=drafts,
    ), 200
