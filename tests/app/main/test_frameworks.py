# -*- coding: utf-8 -*-
import mock
from lxml import html
from dmapiclient import APIError
from ..helpers import BaseApplicationTest


@mock.patch('app.main.views.frameworks.data_api_client', autospec=True)
class TestOpportunitiesDashboard(BaseApplicationTest):
    opportunities_dashboard_url = '/suppliers/opportunities/frameworks/digital-outcomes-and-specialists-2'

    def setup_method(self, method):
        super(TestOpportunitiesDashboard, self).setup_method(method)
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
                'status': 'submitted',
            }
        ]}

    def get_table_rows_by_id(self, table_id, data_api_client):
        """Helper function to get our 3 table rows as strings."""
        data_api_client.get_framework.return_value = self.framework_response
        data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        data_api_client.find_brief_responses.return_value = self.find_brief_responses_response
        with self.client:
            self.login()
            res = self.client.get(self.opportunities_dashboard_url)

            assert res.status_code == 200

            doc = html.fromstring(res.get_data(as_text=True))
            xpath_string = ".//*[@id='{}']/following-sibling::table[1]".format(table_id)
            table = doc.xpath(xpath_string)[0]
            rows = table.find_class('summary-item-row')
            return rows

    def test_request_works_and_correct_data_is_fetched(self, data_api_client):
        data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        data_api_client.get_framework.return_value = self.framework_response
        with self.client:
            self.login()
            resp = self.client.get(self.opportunities_dashboard_url)
            assert resp.status_code == 200
            data_api_client.find_brief_responses.assert_called_once_with(
                supplier_id=1234,
                framework='digital-outcomes-and-specialists-2'
            )

    def test_404_if_framework_does_not_exist(self, data_api_client):
        data_api_client.get_framework.side_effect = APIError(mock.Mock(status_code=404))
        with self.client:
            self.login()
            resp = self.client.get('/suppliers/frameworks/does-not-exist/opportunities')

            assert resp.status_code == 404

    def test_404_if_supplier_framework_does_not_exist(self, data_api_client):
        data_api_client.get_framework.return_value = self.framework_response
        data_api_client.get_supplier_framework_info.side_effect = APIError(mock.Mock(status_code=404))
        with self.client:
            self.login()
            resp = self.client.get(self.opportunities_dashboard_url)

            assert resp.status_code == 404

    def test_404_if_framework_is_not_dos(self, data_api_client):
        self.framework_response['frameworks'].update({'slug': 'g-cloud-9', 'framework': 'g-cloud'})
        data_api_client.get_framework.return_value = self.framework_response
        data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        with self.client:
            self.login()
            resp = self.client.get('/suppliers/frameworks/g-cloud-9/opportunities')

            assert resp.status_code == 404

    def test_404_if_supplier_not_on_framework(self, data_api_client):
        data_api_client.get_framework.return_value = self.framework_response
        self.supplier_framework_response['frameworkInterest'].update(
            {'onFramework': False}
        )
        data_api_client.get_supplier_framework_info.return_value = self.supplier_framework_response
        with self.client:
            self.login()
            resp = self.client.get(self.opportunities_dashboard_url)

            assert resp.status_code == 404

    def test_completed_list_of_opportunities(self, data_api_client):
        """Assert the 'Completed opportunities' table on this page contains the correct values."""
        first_row, second_row, third_row = self.get_table_rows_by_id('submitted-opportunities', data_api_client)

        assert 'Highest date, submitted, lowest id' in first_row.text_content()
        assert first_row.xpath('*//a/@href')[0] == '/suppliers/opportunities/100/responses/result'
        assert 'Thursday 8 June 2017' in first_row.text_content()

    def test_completed_list_of_opportunities_ordered_by_applications_closed_at(self, data_api_client):
        """Assert the 'Completed opportunities' table on this page contains the brief responses in the correct order."""
        first_row, second_row, third_row = self.get_table_rows_by_id('submitted-opportunities', data_api_client)

        assert 'Highest date' in first_row.text_content()
        assert 'Mid date' in second_row.text_content()
        assert 'Lowest date' in third_row.text_content()

    def test_completed_list_of_opportunities_gives_correct_status_for_each_application(self, data_api_client):
        self.find_brief_responses_response = {'briefResponses': [
            {
                'briefId': 1,
                'brief': {
                    'title': 'Submitted brief response for open opportunity',
                    'applicationsClosedAt': '2017-06-09T10:26:21.538917Z',
                    'status': 'live',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 2,
                'brief': {
                    'title': 'Submitted brief response for closed brief',
                    'applicationsClosedAt': '2017-06-08T10:26:21.538917Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 3,
                'brief': {
                    'title': 'Cancelled opportunity',
                    'applicationsClosedAt': '2017-06-07T10:26:21.538917Z',
                    'status': 'cancelled',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 4,
                'brief': {
                    'title': 'Unsuccessful opportunity',
                    'applicationsClosedAt': '2017-06-06T10:26:21.538917Z',
                    'status': 'unsuccessful',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 5,
                'brief': {
                    'title': 'Withdrawn opportunity',
                    'applicationsClosedAt': '2017-06-05T10:26:21.538917Z',
                    'status': 'withdrawn',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 6,
                'brief': {
                    'title': 'Opportunity awarded to this brief response',
                    'applicationsClosedAt': '2017-06-04T10:26:21.538917Z',
                    'status': 'awarded',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'awarded',
            },
            {
                'briefId': 7,
                'brief': {
                    'title': 'Opportunity awarded to a different brief response',
                    'applicationsClosedAt': '2017-06-03T10:26:21.538917Z',
                    'status': 'awarded',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'submitted',
            },
            {
                'briefId': 8,
                'brief': {
                    'title': 'Opportunity pending awarded to this brief response - it should look submitted though',
                    'applicationsClosedAt': '2017-06-02T10:26:21.538917Z',
                    'status': 'closed',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'pending-awarded',
            },
            {
                'briefId': 9,
                'brief': {
                    'title': 'Opportunity pending awarded to this brief response but was then cancelled instead',
                    'applicationsClosedAt': '2017-06-01T10:26:21.538917Z',
                    'status': 'cancelled',
                    'frameworkSlug': 'digital-outcomes-and-specialists-2'
                },
                'status': 'pending-awarded',
            },
        ]}
        rows = self.get_table_rows_by_id('submitted-opportunities', data_api_client)
        statuses = [row.getchildren()[2].text_content().strip() for row in rows]

        assert statuses[0] == 'Submitted'
        assert statuses[1] == 'Submitted'
        assert statuses[2] == 'Opportunity cancelled'
        assert statuses[3] == 'Not won'
        assert statuses[4] == 'Opportunity withdrawn'
        assert statuses[5] == 'Won'
        assert statuses[6] == 'Not won'
        assert statuses[7] == 'Submitted'
        assert statuses[8] == 'Opportunity cancelled'
