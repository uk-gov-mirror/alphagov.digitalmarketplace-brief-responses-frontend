# coding=utf-8

import mock
from .helpers import BaseApplicationTest
from dmapiclient import api_stubs
from dmapiclient.errors import HTTPError


class TestApplication(BaseApplicationTest):
    def setup_method(self, method):
        super(TestApplication, self).setup_method(method)
        self.login()
        self.data_api_client_patch = mock.patch('app.main.views.briefs.data_api_client')
        self.data_api_client = self.data_api_client_patch.start()
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='live')

    def teardown_method(self, method):
        self.data_api_client_patch.stop()

    def test_response_headers(self):
        response = self.client.get('/suppliers/opportunities/1/ask-a-question')

        assert response.status_code == 200
        assert (
            response.headers['cache-control'] ==
            "no-cache"
        )

    def test_url_with_non_canonical_trailing_slash(self):
        response = self.client.get('/suppliers/opportunities/')
        assert response.status_code == 301
        assert "http://localhost/suppliers/opportunities" == response.location

    def test_404(self):
        res = self.client.get('/service/1234')
        assert res.status_code == 404
        assert u"Check you’ve entered the correct web " \
            u"address or start again on the Digital Marketplace homepage." in res.get_data(as_text=True)
        assert u"If you can’t find what you’re looking for, contact us at " \
            u"<a href=\"mailto:enquiries@digitalmarketplace.service.gov.uk?" \
            u"subject=Digital%20Marketplace%20feedback\" title=\"Please " \
            u"send feedback to enquiries@digitalmarketplace.service.gov.uk\">" \
            u"enquiries@digitalmarketplace.service.gov.uk</a>" in res.get_data(as_text=True)

    def test_503(self):
        self.data_api_client.get_brief.side_effect = HTTPError('API is down')
        self.app.config['DEBUG'] = False

        res = self.client.get('/suppliers/opportunities/1/ask-a-question')
        assert res.status_code == 503
        assert u"Sorry, we’re experiencing technical difficulties" in res.get_data(as_text=True)
        assert "Try again later." in res.get_data(as_text=True)

    def test_header_xframeoptions_set_to_deny(self):
        self.login()
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.get('/suppliers/opportunities/1/ask-a-question')
        assert res.status_code == 200
        assert 'DENY', res.headers['X-Frame-Options']

    def test_should_use_local_cookie_page_on_cookie_message(self):
        self.login()
        self.data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.get('/suppliers/opportunities/1/ask-a-question')
        assert res.status_code == 200
        assert '<p>GOV.UK uses cookies to make the site simpler. <a href="/cookies">Find ' \
            'out more about cookies</a></p>' in res.get_data(as_text=True)

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/suppliers/opportunities/static/javascripts/application.js')
        assert res.status_code == 200
        assert 'analytics.trackPageview' in res.get_data(as_text=True)
