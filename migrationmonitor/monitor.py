from Queue import Queue
import threading
import time
import traceback

import libvirt

from actor import actor, POISON_PILL
import db
import utils
import logger as log
import settings

EVENT_DETAILS = (
    ("Added", "Updated"),
    ("Removed",),
    ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup"),
    ("Paused", "Migrated", "IOError", "Watchdog",
        "Restored", "Snapshot", "API error"),
    ("Unpaused", "Migrated", "Snapshot"),
    ("Shutdown", "Destroyed", "Crashed",
        "Migrated", "Saved", "Failed", "Snapshot"),
    ("Finished",),
    ("Memory", "Disk"),
    ("Panicked",),
)

EVENT_STRINGS = (
    "Defined",
    "Undefined",
    "Started",
    "Suspended",
    "Resumed",
    "Stopped",
    "Shutdown",
    "PMSuspended",
    "Crashed",
)

REASON_STRINGS = (
    "Error",
    "End-of-file",
    "Keepalive",
    "Client",
)


class DomainsWatcher(threading.Thread):

    def __init__(self, conn, new_dom_ids_q, lost_dom_ids_q, interval=0.15):
        super(DomainsWatcher, self).__init__()
        self.daemon = True
        self.conn = conn
        self.new_dom_ids_q = new_dom_ids_q
        self.lost_dom_ids_q = lost_dom_ids_q
        self.interval = interval

    def run(self):
        known_dom_ids = set()
        lost_dom_ids = set()

        while True:
            current_dom_ids = self.conn.listDomainsID()
            new_dom_ids = set(current_dom_ids) - known_dom_ids
            lost_dom_ids = known_dom_ids - set(current_dom_ids)

            for dom_id in new_dom_ids:
                self.new_dom_ids_q.put(dom_id)
                known_dom_ids.add(dom_id)
                log.info(
                    "Domain: (%s)%s has found on %s",
                    dom_id,
                    utils.get_dom_name_by_id(self.conn, dom_id),
                    self.conn.getURI())

            for dom_id in lost_dom_ids:
                self.lost_dom_ids_q.put(dom_id)
                known_dom_ids.remove(dom_id)
                log.info(
                    "Domain with id %s was not found on %s",
                    dom_id,
                    self.conn.getURI())

            time.sleep(self.interval)


class DomainsJobMonitor(threading.Thread):

    def __init__(self, conn, new_dom_ids_q, migration_monitors, interval=0.15):
        super(DomainsJobMonitor, self).__init__()
        self.daemon = True
        self.conn = conn
        self.new_dom_ids_q = new_dom_ids_q
        self.migration_monitors = migration_monitors
        self.interval = interval

    def run(self):
        while True:
            if not self.new_dom_ids_q.empty():
                dom_id = self.new_dom_ids_q.get()
                dom_name = utils.get_dom_name_by_id(self.conn, dom_id)

                dom_actor = actor(self._start_dom_job_monitor_actor(
                    self.conn, dom_id))
                self.migration_monitors[dom_id] = dom_actor
                self.migration_monitors[dom_id](
                    ('start_job_monitoring', dom_id))

                log.info(
                    "Start job monitoring for domain (%s)%s on %s",
                    dom_id,
                    utils.get_dom_name_by_id(self.conn, dom_id),
                    self.conn.getURI())
                self.new_dom_ids_q.task_done()

            time.sleep(self.interval)

    def _start_dom_job_monitor_actor(self, conn, dom_id):

        def fn(tell_me, msg):
            cmd, dom_id = msg
            try:
                dom = conn.lookupByID(dom_id)
                job_info = dom.jobStats()
                log.debug("jobStats: {0}".format(job_info))
                db.write(({
                    "domain_id": dom_id,
                    "domain_name": dom.name()},
                    job_info,
                    settings.INFLUXDB["JOBINFO_MEASUREMENT"]))

            except Exception as ex:
                if "Domain not found" not in ex.message:
                    log.error(traceback.format_exc())
            finally:
                time.sleep(settings.LIBVIRT["POLL_FREQ"])
                tell_me(("continue", dom_id))

        dom_name = utils.get_dom_name_by_id(conn, dom_id)
        fn.__name__ = "DomJobMonitor_%s" % (dom_name)
        return fn


class DomainsJobMonitorKiller(threading.Thread):

    def __init__(
            self,
            conn,
            lost_dom_ids_q,
            migration_monitors,
            interval=0.15):

        super(DomainsJobMonitorKiller, self).__init__()
        self.daemon = True
        self.conn = conn
        self.lost_dom_ids_q = lost_dom_ids_q
        self.migration_monitors = migration_monitors
        self.interval = interval

    def run(self):
        while True:
            if not self.lost_dom_ids_q.empty():
                dom_id = self.lost_dom_ids_q.get()
                utils.kill_dom_job_monitor_actor(
                    self.migration_monitors,
                    dom_id)
                self.lost_dom_ids_q.task_done()
            time.sleep(self.interval)


class LibvirtMonitor(object):

    def __init__(self):
        self.connections = []
        self.migration_monitors = {}
        self.new_dom_ids_q = Queue()
        self.lost_dom_ids_q = Queue()

    def start(self):
        for uri in settings.LIBVIRT['URI']:
            self._run(uri)

    def _run(self, uri):
        conn = libvirt.openReadOnly(uri)
        log.info("Connecting to %s", uri)
        self.connections.append(conn)

        self._register_libvirt_callbacks(conn)

        doms_watcher_thread = DomainsWatcher(
            conn,
            self.new_dom_ids_q,
            self.lost_dom_ids_q)
        doms_watcher_thread.start()

        doms_job_monitor_thread = DomainsJobMonitor(
                conn,
                self.new_dom_ids_q,
                self.migration_monitors)
        doms_job_monitor_thread.start()

        doms_job_monitor_killer_thread = DomainsJobMonitorKiller(
            conn,
            self.lost_dom_ids_q,
            self.migration_monitors)
        doms_job_monitor_killer_thread.start()

    def _register_libvirt_callbacks(self, conn):
        conn.registerCloseCallback(self._conn_close_handler, None)
        conn.domainEventRegisterAny(
            None,
            libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
            self._domain_event_handler,
            None)
        conn.setKeepAlive(5, 3)

    def _domain_event_handler(self, conn, dom, event, detail, opaque):
        uri = conn.getURI()
        dom_id = dom.ID()
        dom_name = dom.name()
        log.info("====> (%s)%s %s %s",
                 dom_id,
                 dom_name,
                 EVENT_STRINGS[event],
                 EVENT_DETAILS[event][detail])

        # Migration start events
        started_migrated = (event == 2 and detail == 1) # Started Migrated (on dst)
        suspended_paused = (event == 3 and detail == 0) # Suspended Paused (on src)

        # Migration end events
        resumed_migrated = (event == 4 and detail == 1) # Resumed Migrated (on dst)
        stopped_migrated = (event == 5 and detail == 3) # Stopped Migrated (on src)
        stopped_failed = (event == 5 and detail == 5) # Stopped Failed (on dst)

        boundary_event = stopped_migrated or started_migrated

        db.write(({
            "domain_id": dom_id,
            "domain_name": dom_name,
            "event": EVENT_STRINGS[event],
            "event_detail": EVENT_DETAILS[event][detail]},
            {"value": 1 if boundary_event else 0},
            settings.INFLUXDB["EVENTS_MEASUREMENT"]))

    def _conn_close_handler(self, conn, reason, opaque):
        def reconnect():
            uri = conn.getURI()
            log.debug("Reconnection %s" % (uri,))
            self.connections.remove(conn)
            self._run(uri)

        log.error("Closed connection: %s: %s",
                  conn.getURI(),
                  REASON_STRINGS[reason])
        if reason == 0:
            utils.defer(self.reconnect(),
                        seconds=settings.INFLUXDB["RECONNECT"])

    def stop(self):
        for dom_id in self.migration_monitors:
            utils.kill_dom_job_monitor_actor(self.migration_monitors, dom_id)

        db.write(POISON_PILL)
        for conn in self.connections:
            log.debug("Closing " + conn.getURI())
            conn.close()
