from flask import Blueprint
from dmcontent.content_loader import ContentLoader

main = Blueprint('main', __name__)

content_loader = ContentLoader('app/content')

content_loader.load_manifest('digital-outcomes-and-specialists', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'legacy_edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'legacy_display_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists', 'brief-responses', 'display_brief_response')

content_loader.load_manifest('digital-outcomes-and-specialists-2', 'briefs', 'edit_brief')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'brief-responses', 'edit_brief_response')
content_loader.load_manifest('digital-outcomes-and-specialists-2', 'brief-responses', 'display_brief_response')


@main.after_request
def add_cache_control(response):
    response.cache_control.no_cache = True
    return response


from .views import briefs
from . import errors
