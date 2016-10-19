import pytest

from migrationmonitor.common import actor
from migrationmonitor.common import zmq_publisher_actor


class TestZMQPublisherActor(object):

    def test_init_on_success(self, mocker):
        fake_init = mocker.patch.object(actor.BaseActor, '__init__')
        fake_settings = mocker.patch('migrationmonitor.settings.ZMQ_CONF')

        fake_zmq_socket = mocker.stub()
        fake_zmq_socket.send_multipart = mocker.stub()
        fake_zmq_socket.bind = mocker.stub()

        zmq_PUB = mocker.patch('zmq.PUB')

        fake_zmq_context = mocker.stub()
        fake_zmq_context.socket = mocker.stub()
        fake_zmq_context.socket.return_value = fake_zmq_socket

        Context = mocker.patch('zmq.Context')
        Context.return_value = fake_zmq_context

        zmq_publisher_actor.ZMQPublisherActor()

        fake_init.assert_called_once_with()
        Context.assert_called_once_with()
        fake_zmq_context.socket.assert_called_once_with(zmq_PUB)
        fake_zmq_socket.bind.assert_called_once_with("tcp://%s:%s" %
                                                     (fake_settings["HOST"],
                                                      fake_settings["PORT"]))

    @pytest.fixture
    def init_setup(self, mocker):
        self.fake_zmq_socket = mocker.stub()
        self.fake_zmq_socket.send_multipart = mocker.stub()
        self.fake_zmq_socket.bind = mocker.stub()

        mocker.patch('zmq.PUB')

        self.fake_zmq_context = mocker.stub()
        self.fake_zmq_context.socket = mocker.stub()
        self.fake_zmq_context.socket.return_value = self.fake_zmq_socket

        Context = mocker.patch('zmq.Context')
        Context.return_value = self.fake_zmq_context

    def test_on_receive_on_success(self, mocker, init_setup):
        fake_time = mocker.patch('time.time')
        fake_json_dumps = mocker.patch('json.dumps')

        msg = {
            "tags": {
                "domain_name": "fake_domain_name"
            },
            "values": "fake_value",
            "measurement": "fake_measurement",
        }
        message_body = {
            "fields": msg["values"],
            "measurement": msg["measurement"],
            "tags": msg["tags"],
            "time": fake_time.return_value,
        }

        zmq_pub = zmq_publisher_actor.ZMQPublisherActor()
        zmq_pub._on_receive(msg)

        fake_time.assert_called_once_with()
        self.fake_zmq_socket.send_multipart.assert_called_once_with([
            msg["tags"]["domain_name"],
            fake_json_dumps.return_value])
        fake_json_dumps.assert_called_once_with(message_body)

    def test_stop_on_success(self, mocker, init_setup):
        self.fake_zmq_socket.close = mocker.stub()
        self.fake_zmq_context.term = mocker.stub()

        fake_super = mocker.patch.object(actor.BaseActor, 'stop')
        zmq_pub = zmq_publisher_actor.ZMQPublisherActor()
        zmq_pub.stop()

        self.fake_zmq_socket.close.assert_called_once_with()
        self.fake_zmq_context.term.assert_called_once_with()
        fake_super.assert_called_once_with()
