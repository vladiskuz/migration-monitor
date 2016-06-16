import time
import libvirt
import traceback

from influxdb import InfluxDBClient

from logger import debug, error, info
from actor import actor, POISON_PILL
from util import defer

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
            "time": int(time.time() * 1000000) * 1000,
            "fields": fields
        }]
        client.write_points(json_body)

    return writer


def reporter(influx_settings):
    report_event = create_influx_reporter(influx_settings)
    def fn(tell_me, msg):
        if len(msg) == 3:
            try:
                report_event(*msg)
            except Exception:
                error(traceback.format_exc())
        else:
            debug("Reported received %s instead of triple." % (msg,))

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

    def dom_job_monitor(conn, dom_name):
        _uri = conn.getURI()
        _conn = libvirt.openReadOnly(_uri)
        def fn(tell_me, msg):
            cmd, dom_id = msg
            try:
                dom = _conn.lookupByID(dom_id)
                job_info = dom.jobStats()

                debug("jobStats: {0}".format(job_info))
                tell_reporter(({"domain_id": dom_id,
                                "domain_name": dom_name},
                                job_info,
                                influx_settings["JOBINFO_MEASUREMENT"]))

            except Exception as ex:
                if "Domain not found" not in ex.message:
                    error(traceback.format_exc())
            finally:
                time.sleep(libvirt_settings["POLL_FREQ"])
                tell_me(("continue", dom_id))

        fn.__name__ = "DomJobMonitor_%s" % (dom_name,)
        return fn

    def on_domain_event(conn, dom, event, detail, opaque):
        uri = conn.getURI()
        dom_id = dom.ID()
        dom_name = dom.name()
        info("====> %s(%s) %s %s" % (dom_name, dom_id,
                                    EVENT_STRINGS[event],
                                    EVENT_DETAILS[event][detail]))

        # Migration start events
        started_migrated = (event == 2 and detail == 1) # Started Migrated (on dst)
        suspended_paused = (event == 3 and detail == 0) # Suspended Paused (on src)

        # Migration end events
        resumed_migrated = (event == 4 and detail == 1) # Resumed Migrated (on dst)
        stopped_migrated = (event == 5 and detail == 3) # Stopped Migrated (on src)
        stopped_failed   = (event == 5 and detail == 5) # Stopped Failed (on dst)

        boundary_event = stopped_migrated or started_migrated

        tell_reporter(({"domain_id": dom_id,
                        "domain_name": dom_name,
                        "event": EVENT_STRINGS[event],
                        "event_detail": EVENT_DETAILS[event][detail]},
                       {"value": 1 if boundary_event else 0 },
                       influx_settings["EVENTS_MEASUREMENT"]))

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

        ds = vc.listDomainsID()
        m = migration_monitors

        for d_id in ds:
            dom = vc.lookupByID(d_id)
            dom_name = dom.name()
            m[dom_name] = actor(dom_job_monitor(vc, dom_name))
            m[dom_name](('go', d_id))



    for u in libvirt_uris:
        connect(u)

    def closer():
        for dom_name in migration_monitors:
            migration_monitors[dom_name](POISON_PILL)
            debug("Sending poison pill to monitoring process for domain:%s" % dom_name)

        tell_reporter(POISON_PILL)
        for c in connections:
            debug("Closing " + c.getURI())
            c.close()

    return closer

