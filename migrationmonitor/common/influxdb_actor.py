import time
import traceback

import influxdb

from migrationmonitor import settings
from migrationmonitor.common import actor
from migrationmonitor.common import logger as log


class InfluxDBActor(actor.BaseActor):

    def __init__(self):
        super(InfluxDBActor, self).__init__()
        self.influx_conf = settings.INFLUXDB_CONF
        self.db_client = influxdb.InfluxDBClient(
            self.influx_conf["HOST"],
            self.influx_conf["PORT"],
            self.influx_conf["USERNAME"],
            self.influx_conf["PASSWORD"],
            self.influx_conf["DATABASE"])

    def _on_receive(self, msg):
        if len(msg) >= 3:
            try:
                self._write(**msg)
            except:
                log.error(traceback.format_exc())
        else:
            log.error("Reported received %s instead of triple." % (msg,))

    def _write(self, tags, values, measurement, datetime=None):
        tags.update(self.influx_conf["TAGS"])

        timestamp = time.time() \
            if datetime is None \
            else time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6

        json_body = [{
            "fields": values,
            "measurement": measurement,
            "tags": tags,
            "time": int(timestamp * 1000000) * 1000,
        }]
        self.db_client.write_points(json_body)
