import json
import time

import zmq

from migrationmonitor import settings
from migrationmonitor.common import actor


class ZMQPublisherActor(actor.BaseActor):

    def __init__(self):
        super(ZMQPublisherActor, self).__init__()
        self.zmq_conf = settings.ZMQ_CONF
        self.zmq_context = zmq.Context()
        self.socket = self.zmq_context.socket(zmq.PUB)
        self.socket.bind("tcp://%s:%s" %
                         (self.zmq_conf["HOST"],
                          self.zmq_conf["PORT"]))

    def _on_receive(self, msg):
        domain_name = msg["tags"]["domain_name"]

        message_body = {
            "fields": msg["values"],
            "measurement": msg["measurement"],
            "tags": msg["tags"],
            "time": time.time(),
        }

        self.socket.send_multipart([domain_name, json.dumps(message_body)])

    def stop(self):
        self.socket.close()
        self.zmq_context.term()
        super(ZMQPublisherActor, self).stop()
