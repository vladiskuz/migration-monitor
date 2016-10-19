from migrationmonitor import settings
from migrationmonitor.common import actor
from migrationmonitor.common import reporter


class TestReporter(object):

    def test_init_on_success(self, mocker):
        influx_reporter = mocker.stub()
        influx_reporter.start = mocker.stub()

        InfluxDBActor = mocker.stub()
        InfluxDBActor.return_value = influx_reporter

        zmq_reporter = mocker.stub()
        zmq_reporter.start = mocker.stub()

        ZMQPublisherActor = mocker.stub()
        ZMQPublisherActor.return_value = zmq_reporter

        settings.REPORT_TO = [settings.INFLUXDB, settings.ZMQ]

        reporter.REPORTERS_MAP = {
            settings.INFLUXDB: InfluxDBActor,
            settings.ZMQ: ZMQPublisherActor
        }

        common_reporter = reporter.Reporter()

        InfluxDBActor.assert_called_once_with()
        influx_reporter.start.assert_called_once_with()

        ZMQPublisherActor.assert_called_once_with()
        zmq_reporter.start.assert_called_once_with()

        assert influx_reporter in common_reporter.reporters
        assert zmq_reporter in common_reporter.reporters

    def test_on_receive_on_success(self, mocker):
        settings.REPORT_TO = []

        reporter_one = mocker.stub()
        reporter_one.tell = mocker.stub()

        reporter_two = mocker.stub()
        reporter_two.tell = mocker.stub()

        fake_msg = mocker.stub()

        common_reporter = reporter.Reporter()
        common_reporter.reporters = [reporter_one, reporter_two]

        common_reporter._on_receive(fake_msg)

        reporter_one.tell.assert_called_once_with(fake_msg)
        reporter_two.tell.assert_called_once_with(fake_msg)

    def test_stop_on_success(self, mocker):
        settings.REPORT_TO = []

        reporter_one = mocker.stub()
        reporter_one.stop = mocker.stub()

        reporter_two = mocker.stub()
        reporter_two.stop = mocker.stub()

        fake_super = mocker.patch.object(actor.BaseActor, 'stop')

        common_reporter = reporter.Reporter()
        common_reporter.reporters = [reporter_one, reporter_two]

        common_reporter.stop()

        reporter_one.stop.assert_called_once_with()
        reporter_two.stop.assert_called_once_with()
        fake_super.assert_called_once_with()
