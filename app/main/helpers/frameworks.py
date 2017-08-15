# -*- coding: utf-8 -*-
from flask import abort


def get_framework(client, framework_slug, allowed_statuses=None):
    if allowed_statuses is None:
        allowed_statuses = ['open', 'pending', 'standstill', 'live']

    framework = client.get_framework(framework_slug)['frameworks']

    if allowed_statuses and framework['status'] not in allowed_statuses:
        abort(404)

    return framework


def get_framework_and_lot(client, framework_slug, lot_slug, allowed_statuses=None):
    framework = get_framework(client, framework_slug, allowed_statuses)
    return framework, get_framework_lot(framework, lot_slug)


def get_framework_lot(framework, lot_slug):
    try:
        return next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)
