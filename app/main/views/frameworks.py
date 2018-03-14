# coding: utf-8

from flask import render_template, abort
from flask_login import current_user
from dmapiclient import APIError
from ... import data_api_client
from ...main import main
from ..helpers import login_required


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
        supplier_id=current_user.supplier_id, framework=framework_slug
    )['briefResponses']

    return render_template(
        "frameworks/opportunities_dashboard.html",
        framework=framework,
        completed=opportunities
    ), 200
