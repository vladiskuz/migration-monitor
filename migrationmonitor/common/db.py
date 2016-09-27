import time
import traceback

from influxdb import InfluxDBClient

from migrationmonitor import settings
from migrationmonitor.common import logger as log
from migrationmonitor.common.actor import BaseActor


class InfluxDBActor(BaseActor):

    def __init__(self):
        super(InfluxDBActor, self).__init__()
        self.influx_settings = settings.INFLUXDB
        self.db_client = InfluxDBClient(self.influx_settings["HOST"],
                                        self.influx_settings["PORT"],
                                        self.influx_settings["USERNAME"],
                                        self.influx_settings["PASSWORD"],
                                        self.influx_settings["DATABASE"])

    def _on_receive(self, msg):
        if len(msg) >= 3:
            try:
                self._write(*msg)
            except:
                log.error(traceback.format_exc())
        else:
            log.error("Reported received %s instead of triple." % (msg,))

    def _write(self, tags, fields, measurement, dt=None):
        tags.update(self.influx_settings["TAGS"])

        timestamp = time.time() \
            if dt is None \
            else time.mktime(dt.timetuple()) + dt.microsecond / 1E6


        json_body = [{
            "measurement": measurement,
            "tags": tags,
            "time": int(timestamp * 1000000) * 1000,
            "fields": fields
        }]
        self.db_client.write_points(json_body)
