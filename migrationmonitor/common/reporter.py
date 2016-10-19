from migrationmonitor import settings
from migrationmonitor.common import actor
from migrationmonitor.common import influxdb_actor
from migrationmonitor.common import zmq_publisher_actor

REPORTERS_MAP = {
    settings.INFLUXDB: influxdb_actor.InfluxDBActor,
    settings.ZMQ: zmq_publisher_actor.ZMQPublisherActor
}


class Reporter(actor.BaseActor):

    def __init__(self):
        super(Reporter, self).__init__()
        self.reporters = []
        self.report_to = settings.REPORT_TO

        for reporter_name in self.report_to:
            reporter_class = REPORTERS_MAP[reporter_name]
            reporter = reporter_class()
            reporter.start()
            self.reporters.append(reporter)

    def _on_receive(self, msg):
        for reporter in self.reporters:
            reporter.tell(msg)

    def stop(self):
        for reporter in self.reporters:
            reporter.stop()
        super(Reporter, self).stop()
