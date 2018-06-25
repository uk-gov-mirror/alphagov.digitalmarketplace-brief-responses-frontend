# coding: utf-8

from flask import render_template, abort
from flask_login import current_user
from dmapiclient import APIError
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
        supplier_id=current_user.supplier_id, framework=framework_slug, status=",".join(BRIEF_RESPONSE_STATUSES)
    )['briefResponses']

    # Split into two tables by status
    drafts, completed = [], []
    for opportunity in opportunities:
        if opportunity['status'] == 'draft':
            drafts.append(opportunity)
        else:
            completed.append(opportunity)

    return render_template(
        "frameworks/opportunities_dashboard.html",
        framework=framework,
        completed=completed,
        drafts=drafts,
    ), 200
