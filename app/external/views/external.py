from flask import Blueprint

external = Blueprint('external', __name__)


@external.route('/suppliers')
def dashboard():
    raise NotImplementedError()


@external.route('/suppliers/frameworks/<framework_slug>/opportunities')
def opportunities_dashboard():
    raise NotImplementedError()
