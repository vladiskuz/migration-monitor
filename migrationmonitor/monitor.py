import traceback
from datetime import datetime as dt

import libvirt
from influxdb import InfluxDBClient

from logger import debug, error, info
from actor import actor, POISON_PILL
from util import defer
import time

EVENT_DETAILS = (("Added", "Updated"),
                 ("Removed",),
                 ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup"),
                 ("Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error"),
                 ("Unpaused", "Migrated", "Snapshot"),
                 ("Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot"),
                 ("Finished",),
                 ("Memory", "Disk"),
                 ("Panicked",),
                 )

EVENT_STRINGS = ("Defined",
                 "Undefined",
                 "Started",
                 "Suspended",
                 "Resumed",
                 "Stopped",
                 "Shutdown",
                 "PMSuspended",
                 "Crashed",
                 )

REASON_STRINGS = ("Error",
                  "End-of-file",
                  "Keepalive",
                  "Client",
                  )


def create_influx_reporter(influx_settings):
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
            "time": dt.now(),
            "fields": fields
        }]
        client.write_points(json_body)

    return writer


def reporter(influx_settings):
    report_event = create_influx_reporter(influx_settings)

    def fn(tell_me, msg):
        if len(msg) == 4:
            try:
                report_event(*msg)
            except Exception:
                error(traceback.format_exc())
        else:
            debug("Reported received %s instead of 4-tuple." % (msg,))

    fn.__name__ = "Reporter"
    return fn


def monitor_libvirt_events(libvirt_settings, influx_settings):
    libvirt_uris = libvirt_settings['URI']
    connections = []
    migration_monitors = {}

    tell_reporter = actor(reporter(influx_settings))

    def reconnect(conn):
        def reconnect_fn():
            uri = conn.getURI()
            debug("Reconnection %s" % (uri,))
            connections.remove(conn)
            connect(uri)

        return reconnect_fn

    def dom_job_monitor(dom):
        dom_id = dom.ID()
        dom_name = dom.name()

        def fn(tell_me, msg):
            try:
                job_info = dom.jobInfo()
                tell_reporter(({"type": job_info[0],
                                "domain_id": dom_id,
                                "domain_name": dom_name},
                               {"time_elapsed": job_info[1],
                                "time_remaining": job_info[2],
                                "data_total": job_info[3],
                                "data_processed": job_info[4],
                                "data_remaining": job_info[5],
                                "mem_total": job_info[6],
                                "mem_processed": job_info[7],
                                "mem_remaining": job_info[8],
                                "file_total": job_info[9],
                                "file_processed": job_info[10],
                                "file_remaining": job_info[11]},
                               influx_settings["JOBINFO_MEASUREMENT"]))

                debug("Domain: %s data_processed:%s" % (dom_name, job_info[4]))
            except Exception:
                error(traceback.format_exc())
            finally:
                tell_me("continue")
                time.sleep(libvirt_settings["POLL_FREQ"])

        fn.__name__ = "DomJobMonitor_%s" % (dom_name,)
        return fn

    def on_domain_event(conn, dom, event, detail, opaque):
        uri = conn.getURI()
        dom_id = dom.ID()
        dom_name = dom.name()
        debug("%s: %s(%s) %s %s" % (uri, dom_name, dom_id,
                                    EVENT_STRINGS[event],
                                    EVENT_DETAILS[event][detail]))

        border_event = (event == 5 and detail == 3) or (event == 2 and detail == 1)

        tell_reporter(({"domain_id": dom_id,
                        "domain_name": dom_name,
                        "event": EVENT_STRINGS[event],
                        "event_detail": EVENT_DETAILS[event][detail]},
                       {"value": 1 if border_event else 0 },
                       influx_settings["EVENTS_MEASUREMENT"]))

        m = migration_monitors

        #  Started Migrated                 Suspended  Paused
        if (event == 2 and detail == 1) or (event == 3 and detail == 0) :
            if dom_name in m:
                m[dom_name](POISON_PILL)
            else:
                m[dom_name] = {}

            m[dom_name] = actor(dom_job_monitor(dom))
            m[dom_name]('go')

            info("Migration for libvirt:%s for domain:%s STARTED." % (uri, dom_name))
            debug("Starting monitoring for domain:%s" % dom_name)
        # Resumed Migrated                    Stopped Migrated
        elif (event == 4 and detail == 1) or (event == 5 and detail == 3):
            if dom_name not in m:
                error("Error, received stop event for migration not being monitored.")
            else:
              info("Migration for libvirt:%s for domain:%s STOPPED." % (uri, dom_name))
              m[dom_name](POISON_PILL)
              debug("Sending poison pill to monitoring process for domain:%s" % dom_name)

    def on_conn_close(conn, reason, opaque):
        error("Closed connection: %s: %s" % (conn.getURI(),
                                             REASON_STRINGS[reason]))

        if reason == 0:
            defer(reconnect(conn),
                  seconds=influx_settings["RECONNECT"])

    def connect(uri):
        vc = libvirt.openReadOnly(uri)
        vc.registerCloseCallback(on_conn_close, None)
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, on_domain_event, None)
        vc.setKeepAlive(5, 3)
        connections.append(vc)

    for u in libvirt_uris:
        connect(u)

    def closer():
        tell_reporter(POISON_PILL)
        for c in connections:
            debug("Closing " + c.getURI())
            c.close()

    return closer
