from app.main import main
from dmapiclient import APIError
from dmcontent.content_loader import QuestionNotFoundError
from dmutils.errors import render_error_page


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return render_error_page(e)


@main.app_errorhandler(QuestionNotFoundError)
def content_loader_error_handler(e):
    return render_error_page(400)
