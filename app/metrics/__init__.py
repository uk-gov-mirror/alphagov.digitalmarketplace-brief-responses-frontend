from flask import Blueprint
from flask.signals import got_request_exception, request_finished

from gds_metrics import GDSMetrics


metrics = Blueprint('metrics', __name__)


class DMGDSMetrics(GDSMetrics):

    def init_app(self, app):
        app.before_request(self.before_request)
        request_finished.connect(self.teardown_request, sender=app)
        got_request_exception.connect(self.handle_exception, sender=app)


gds_metrics = DMGDSMetrics()

metrics.add_url_rule(gds_metrics.metrics_path, 'metrics', gds_metrics.metrics_endpoint)
