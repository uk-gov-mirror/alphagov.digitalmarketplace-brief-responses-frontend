from flask import Blueprint

external = Blueprint('external', __name__)


@external.route('/suppliers')
def dashboard():
    raise NotImplementedError()
