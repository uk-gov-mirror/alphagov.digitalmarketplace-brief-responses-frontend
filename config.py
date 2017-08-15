# coding=utf-8

import os
import jinja2
from dmutils.status import enabled_since, get_version_label
from dmutils.asset_fingerprint import AssetFingerprinter


class Config(object):

    VERSION = get_version_label(
        os.path.abspath(os.path.dirname(__file__))
    )
    SESSION_COOKIE_NAME = 'dm_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

    PERMANENT_SESSION_LIFETIME = 4 * 3600

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    DM_DATA_API_URL = None
    DM_DATA_API_AUTH_TOKEN = None
    DM_MANDRILL_API_KEY = None

    DEBUG = False

    CLARIFICATION_EMAIL_NAME = 'Digital Marketplace Admin'
    CLARIFICATION_EMAIL_FROM = 'do-not-reply@digitalmarketplace.service.gov.uk'

    SECRET_KEY = None

    STATIC_URL_PATH = '/suppliers/opportunities/static'
    ASSET_PATH = STATIC_URL_PATH + '/'
    BASE_TEMPLATE_DATA = {
        'header_class': 'with-proposition',
        'asset_path': ASSET_PATH,
        'asset_fingerprinter': AssetFingerprinter(asset_root=ASSET_PATH)
    }

    # Feature Flags
    RAISE_ERROR_ON_MISSING_FEATURES = True

    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = False

    # Logging
    DM_LOG_LEVEL = 'DEBUG'
    DM_PLAIN_TEXT_LOGS = False
    DM_LOG_PATH = None
    DM_APP_NAME = 'brief-responses-frontend'
    DM_DOWNSTREAM_REQUEST_ID_HEADER = 'X-Amz-Cf-Id'

    @staticmethod
    def init_app(app):
        repo_root = os.path.abspath(os.path.dirname(__file__))
        template_folders = [
            os.path.join(repo_root, 'app/templates')
        ]
        jinja_loader = jinja2.FileSystemLoader(template_folders)
        app.jinja_loader = jinja_loader


class Test(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    DM_LOG_LEVEL = 'CRITICAL'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    DM_MANDRILL_API_KEY = 'MANDRILL'
    SECRET_KEY = 'verySecretKey'

    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = enabled_since('2016-11-29')

    DM_DATA_API_AUTH_TOKEN = 'myToken'


class Development(Config):
    DEBUG = True
    DM_PLAIN_TEXT_LOGS = True
    SESSION_COOKIE_SECURE = False

    # Dates not formatted like YYYY-(0)M-(0)D will fail
    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = enabled_since('2016-11-29')

    DM_DATA_API_URL = "http://localhost:5000"
    DM_DATA_API_AUTH_TOKEN = "myToken"
    DM_API_AUTH_TOKEN = "myToken"

    DM_MANDRILL_API_KEY = "not_a_real_key"
    SECRET_KEY = 'verySecretKey'


class Live(Config):
    """Base config for deployed environments"""
    DEBUG = False
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'
    DM_HTTP_PROTO = 'https'


class Preview(Live):
    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = enabled_since('2017-02-06')


class Production(Live):
    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = enabled_since('2017-02-08')


class Staging(Production):
    FEATURE_FLAGS_NEW_SUPPLIER_FLOW = enabled_since('2017-02-07')


configs = {
    'development': Development,
    'preview': Preview,
    'staging': Staging,
    'production': Production,
    'test': Test,
}
