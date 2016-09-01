import time
import traceback

from influxdb import InfluxDBClient

from actor import actor
import logger as log
import settings

def _create_influx_reporter(influx_settings):
    client = InfluxDBClient(influx_settings["HOST"],
                            influx_settings["PORT"],
                            influx_settings["USERNAME"],
                            influx_settings["PASSWORD"],
                            influx_settings["DATABASE"])

    def writer(tags, fields, measurement):
        tags.update(influx_settings["TAGS"])
        json_body = [{
            "measurement": measurement,
            "tags": tags,
            "time": int(time.time() * 1000000) * 1000,
            "fields": fields
        }]
        client.write_points(json_body)

    return writer


def _reporter():
    report_event = _create_influx_reporter(settings.INFLUXDB)

    def fn(tell_me, msg):
        if len(msg) == 3:
            try:
                report_event(*msg)
            except Exception:
                log.error(traceback.format_exc())
        else:
            log.debug("Reported received %s instead of triple." % (msg,))

    fn.__name__ = "Reporter"
    return fn

write = actor(_reporter())
