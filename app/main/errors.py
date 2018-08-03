try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus
from flask import redirect, render_template, request, url_for, session, current_app, flash
from flask_wtf.csrf import CSRFError
from app.main import main
from dmapiclient import APIError
from dmcontent.content_loader import QuestionNotFoundError


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return _render_error_page(e.status_code)


@main.app_errorhandler(QuestionNotFoundError)
def content_loader_error_handler(e):
    return _render_error_page(400)


@main.app_errorhandler(401)
def page_unauthorized(e):
    if request.method == 'GET':
        return redirect('/user/login?next={}'.format(quote_plus(request.path)))
    else:
        return redirect('/user/login')


@main.app_errorhandler(404)
def page_not_found(e):
    return _render_error_page(404)


@main.app_errorhandler(500)
def internal_server_error(e):
    return _render_error_page(500)


@main.app_errorhandler(503)
def service_unavailable(e):
    return _render_error_page(503)


@main.app_errorhandler(400)
def csrf_handler(e):
    # CSRFErrors seem to be propagated as '400 Bad Request' exceptions, which means Flask is looking for
    # a 400 handler rather than a specific CSRFError handler.
    # This heavy-handed solution therefore catches all 400s, but immediately discards non-CSRFError instances.
    if not isinstance(e, CSRFError):
        raise e

    if 'user_id' not in session:
        current_app.logger.info(
            u'csrf.session_expired: Redirecting user to log in page'
        )
    else:
        current_app.logger.info(
            u'csrf.invalid_token: Aborting request, user_id: {user_id}',
            extra={'user_id': session['user_id']}
        )

    flash('Your session has expired. Please log in again.', "error")
    return redirect(url_for('external.render_login', next=request.path))


def _render_error_page(status_code):
    template_map = {
        400: "errors/500.html",
        404: "errors/404.html",
        500: "errors/500.html",
        503: "errors/500.html",
    }
    if status_code not in template_map:
        status_code = 500
    return render_template(template_map[status_code]), status_code
