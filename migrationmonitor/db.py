import time
import traceback

from influxdb import InfluxDBClient

import actor
import logger as log
import settings


class InfluxDBActor(actor.BaseActor):

    def __init__(self):
        super(InfluxDBActor, self).__init__()
        self.influx_settings = settings.INFLUXDB
        self.db_client = InfluxDBClient(self.influx_settings["HOST"],
                                        self.influx_settings["PORT"],
                                        self.influx_settings["USERNAME"],
                                        self.influx_settings["PASSWORD"],
                                        self.influx_settings["DATABASE"])

    def _on_receive(self, msg):
        if len(msg) == 3:
            try:
                self._write(*msg)
            except Exception:
                log.error(traceback.format_exc())
        else:
            log.debug("Reported received %s instead of triple." % (msg,))

    def _write(self, tags, fields, measurement):
        tags.update(self.influx_settings["TAGS"])
        json_body = [{
            "measurement": measurement,
            "tags": tags,
            "time": int(time.time() * 1000000) * 1000,
            "fields": fields
        }]
        self.db_client.write_points(json_body)
