from functools import partial
from flask import Blueprint
from dmcontent.content_loader import ContentLoader
from dmutils.access_control import require_login

main = Blueprint('main', __name__)
public = Blueprint('public', __name__)  # Supplier login not required

content_loader = ContentLoader('app/content')

content_loader.load_manifest('digital-outcomes-and-specialists', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'legacy_edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'legacy_display_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'display_brief_response')

content_loader.load_manifest('digital-outcomes-and-specialists-2', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'brief-responses', 'display_brief_response')

content_loader.load_manifest('digital-outcomes-and-specialists-3', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists-3', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists-3', 'brief-responses', 'display_brief_response')

content_loader.load_manifest('digital-outcomes-and-specialists-4', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists-4', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists-4', 'brief-responses', 'display_brief_response')

main.before_request(partial(require_login, role='supplier'))


@main.after_request
def add_cache_control(response):
    response.cache_control.no_cache = True
    return response


from .views import briefs, frameworks
from . import errors
