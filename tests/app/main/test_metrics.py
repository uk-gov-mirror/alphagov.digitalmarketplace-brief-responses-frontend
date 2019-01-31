# -*- coding: utf-8 -*-
import mock
import re

from dmtestutils.api_model_stubs import BriefStub

from tests.app.helpers import BaseApplicationTest


def load_prometheus_metrics(response_bytes):
    return dict(re.findall(b"(\w+{.+?}) (\d+)", response_bytes))


class TestMetricsPage(BaseApplicationTest):

    def test_metrics_page_accessible(self):
        metrics_response = self.client.get('/suppliers/opportunities/_metrics')

        assert metrics_response.status_code == 200

    def test_metrics_page_contents(self):
        metrics_response = self.client.get('/suppliers/opportunities/_metrics')
        results = load_prometheus_metrics(metrics_response.data)

        assert (
            b'http_server_requests_total{code="200",host="localhost.localdomain",method="GET",'
            b'path="/suppliers/opportunities/_metrics"}'
        ) in results


class TestMetricsPageRegistersPageViews(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client_patch = mock.patch('app.main.views.briefs.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    def test_metrics_page_registers_page_views(self):
        expected_metric_name = (
            b'http_server_requests_total{code="200",host="localhost.localdomain",'
            b'method="GET",path="/suppliers/opportunities/'
            b'<int:brief_id>/question-and-answer-session"}'
        )

        self.login()
        self.data_api_client.get_brief.return_value = BriefStub(status='live').single_result_response()

        res = self.client.get('/suppliers/opportunities/1/question-and-answer-session')
        assert res.status_code == 200

        metrics_response = self.client.get('/suppliers/opportunities/_metrics')
        results = load_prometheus_metrics(metrics_response.data)
        assert expected_metric_name in results

    def test_metrics_page_registers_multiple_page_views(self):
        expected_metric_name = (
            b'http_server_requests_total{code="200",host="localhost.localdomain",'
            b'method="GET",path="/suppliers/opportunities/'
            b'<int:brief_id>/question-and-answer-session"}'
        )

        initial_metrics_response = self.client.get('/suppliers/opportunities/_metrics')
        initial_results = load_prometheus_metrics(initial_metrics_response.data)
        initial_metric_value = int(initial_results.get(expected_metric_name, 0))

        self.login()
        self.data_api_client.get_brief.return_value = BriefStub(status='live').single_result_response()

        for _ in range(3):
            res = self.client.get('/suppliers/opportunities/1/question-and-answer-session')
            assert res.status_code == 200

        metrics_response = self.client.get('/suppliers/opportunities/_metrics')
        results = load_prometheus_metrics(metrics_response.data)
        metric_value = int(results.get(expected_metric_name, 0))

        assert expected_metric_name in results
        assert metric_value - initial_metric_value is 3
