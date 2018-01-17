from flask import Blueprint

external = Blueprint('external', __name__)


@external.route('/suppliers')
def dashboard():
    raise NotImplementedError()


@external.route('/<string:framework_framework>/opportunities/<int:brief_id>/')
def buyer_frontend_get_brief_by_id(framework_framework, brief_id):
    raise NotImplementedError()


@external.route('/help')
def help():
    raise NotImplementedError()
