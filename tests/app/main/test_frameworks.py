# -*- coding: utf-8 -*-
import pytest
import mock
from freezegun import freeze_time
from lxml import html
from dmapiclient import APIError
from ..helpers import BaseApplicationTest


class TestOpportunitiesDashboard(BaseApplicationTest):
    opportunities_dashboard_url = '/suppliers/opportunities/frameworks/digital-outcomes-and-specialists-2'

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.frameworks.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.framework_response = {
            'frameworks': {
                'slug': 'digital-outcomes-and-specialists-2',
                'framework': 'digital-outcomes-and-specialists'
            }
        }
        self.supplier_framework_response = {
            'frameworkInterest': {'onFramework': True}
        }
        self.find_brief_responses_response = {'briefResponses': [
            {
                'briefId': 100,
                'brief': {
                    'title': 'Highest date, submitted, lowest id',
                    'applicationsClosedAt': '2017-06-08T10:26:21.538917Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 1,
                'status': 'submitted',
            },
            {
                'briefId': 1829,
                'brief': {
                    'title': 'Lowest date, submitted, mid id',
                    'applicationsClosedAt': '2017-06-06T10:26:21.538917Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 2,
                'status': 'submitted',
            },
            {
                'briefId': 4734,
                'brief': {
                    'title': 'Mid date, submitted, highest id',
                    'applicationsClosedAt': '2017-06-07T10:26:21.538917Z',
                    'status': 'withdrawn',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 3,
                'status': 'submitted',
            },
            {
                'briefId': 5653,
                'brief': {
                    'title': 'Highest date, draft',
                    'applicationsClosedAt': '2017-06-07T10:26:21.538917Z',
                    'status': 'live',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 4,
                'status': 'draft',
            },
            {
                'briefId': 9999,
                'brief': {
                    'title': 'Lowest date, draft',
                    'applicationsClosedAt': '2017-06-05T10:26:21.538917Z',
                    'status': 'live',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 5,
                'status': 'draft',
            },
            {
                'briefId': 9998,
                'brief': {
                    'title': 'Middle date, draft',
                    'applicationsClosedAt': '2017-06-06T10:26:21.538917Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 6,
                'status': 'draft',
            },
            {
                'briefId': 9997,
                'brief': {
                    'title': 'Ancient date, draft',
                    'applicationsClosedAt': '2017-06-01T23:59:59.999999Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'id': 7,
                'status': 'draft',
            }
        ]}
        self.login()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def get_table_rows_by_id(self, table_id):
        """Helper function to get our 3 table rows as strings."""
        self.data_api_client.get_framework.return_value = self.framework_response
        self.data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        self.data_api_client.find_brief_responses.return_value = self.find_brief_responses_response

        res = self.client.get(self.opportunities_dashboard_url)

        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        xpath_string = ".//*[@id='{}']/following-sibling::table[1]".format(table_id)
        table = doc.xpath(xpath_string)[0]
        rows = table.find_class('summary-item-row')
        return rows

    def test_request_works_and_correct_data_is_fetched(self):
        self.data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        self.data_api_client.get_framework.return_value = self.framework_response

        resp = self.client.get(self.opportunities_dashboard_url)
        assert resp.status_code == 200
        self.data_api_client.find_brief_responses.assert_called_once_with(
            supplier_id=1234,
            framework='digital-outcomes-and-specialists-2',
            status='draft,submitted,pending-awarded,awarded'
        )

    def test_404_if_framework_does_not_exist(self):
        self.data_api_client.get_framework.side_effect = APIError(mock.Mock(status_code=404))

        resp = self.client.get('/suppliers/frameworks/does-not-exist/opportunities')

        assert resp.status_code == 404

    def test_404_if_supplier_framework_does_not_exist(self):
        self.data_api_client.get_framework.return_value = self.framework_response
        self.data_api_client.get_supplier_framework_info.side_effect = APIError(mock.Mock(status_code=404))

        resp = self.client.get(self.opportunities_dashboard_url)

        assert resp.status_code == 404

    def test_404_if_framework_is_not_dos(self):
        self.framework_response['frameworks'].update({'slug': 'g-cloud-9', 'framework': 'g-cloud'})
        self.data_api_client.get_framework.return_value = self.framework_response
        self.data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response

        resp = self.client.get('/suppliers/frameworks/g-cloud-9/opportunities')

        assert resp.status_code == 404

    def test_404_if_supplier_not_on_framework(self):
        self.data_api_client.get_framework.return_value = self.framework_response
        self.supplier_framework_response['frameworkInterest'].update(
            {'onFramework': False}
        )
        self.data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response

        resp = self.client.get(self.opportunities_dashboard_url)

        assert resp.status_code == 404

    def test_completed_list_of_opportunities(self):
        """Assert the 'Completed opportunities' table on this page contains the correct values."""
        first_row, second_row, third_row = self.get_table_rows_by_id('submitted-opportunities')

        assert 'Highest date, submitted, lowest id' in first_row.text_content()
        assert first_row.xpath('*//a/@href')[0] == '/suppliers/opportunities/100/responses/1/application'
        assert 'Thursday 8 June 2017' in first_row.text_content()

    def test_completed_list_of_opportunities_ordered_by_applications_closed_at(self):
        """Assert the 'Completed opportunities' table on this page contains the brief responses in the correct order."""
        first_row, second_row, third_row = self.get_table_rows_by_id('submitted-opportunities')

        assert 'Highest date' in first_row.text_content()
        assert 'Mid date' in second_row.text_content()
        assert 'Lowest date' in third_row.text_content()

    def test_draft_list_of_opportunities_ordered_by_applications_closed_at(self):
        """Assert the 'Draft opportunities' table on this page contains the brief responses in the correct order."""
        with freeze_time('2017-06-16'):
            first_row, second_row, third_row = self.get_table_rows_by_id('draft-opportunities')

        # 'Ancient date' is not shown, as it is for a non-live brief over 2 weeks old
        assert 'Lowest date' in first_row.text_content()
        assert 'Middle date' in second_row.text_content()
        assert 'Highest date' in third_row.text_content()

    def _get_brief_response_dashboard_status(self, brief_response_status, brief_status, application_state='submitted'):
        self.find_brief_responses_response = {
            'briefResponses': [
                {
                    'briefId': 1,
                    'brief': {
                        'title': f'{brief_response_status} brief response for {brief_status} opportunity',
                        'applicationsClosedAt': '2017-06-09T10:26:21.538917Z',
                        'status': brief_status,
                        'frameworkSlug': 'digital-outcomes-and-specialists-2'
                    },
                    'id': 999,
                    'status': brief_response_status,
                },
            ]
        }
        return self.get_table_rows_by_id(f'{application_state}-opportunities')

    @pytest.mark.parametrize(
        'brief_response_status, brief_status, display_status',
        [
            ("submitted", "live", "Submitted"),
            ("submitted", "closed", "Submitted"),
            ("submitted", "cancelled", "Opportunity cancelled"),
            ("submitted", "unsuccessful", "Not won"),
            ("submitted", "withdrawn", "Opportunity withdrawn"),
            ("submitted", "awarded", "Not won"),
            ("pending-awarded", "closed", "Submitted"),
            ("pending-awarded", "cancelled", "Opportunity cancelled"),
            ("awarded", "awarded", "Won"),
        ]
    )
    def test_completed_brief_response_for_each_brief_status_shows_display_status(
        self, brief_response_status, brief_status, display_status
    ):
        rows = self._get_brief_response_dashboard_status(brief_response_status, brief_status)
        assert [row.getchildren()[2].text_content().strip() for row in rows][0] == display_status

    def test_draft_brief_response_for_live_briefs_shows_link(self):
        rows = self._get_brief_response_dashboard_status('draft', 'live', application_state='draft')

        assert [row.getchildren()[2].text_content().strip() for row in rows][0] == "Draft"
        assert [row.getchildren()[3].text_content().strip() for row in rows][0] == "Complete your application"

    @pytest.mark.parametrize('brief_status', ['closed', 'cancelled', 'unsuccessful', 'withdrawn', 'awarded'])
    def test_draft_brief_response_for_non_live_briefs_shows_applications_closed_message(self, brief_status):
        with freeze_time('2017-06-23 10:26:21'):
            rows = self._get_brief_response_dashboard_status('draft', brief_status, application_state='draft')

        assert [row.getchildren()[2].text_content().strip() for row in rows][0] == "Draft"
        assert [row.getchildren()[3].text_content().strip() for row in rows][0] == "Applications closed"
