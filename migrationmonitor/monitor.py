import threading

import libvirt

import db
import utils
import logger as log
import settings
import watcher

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

REASON_STRINGS = ("Error", "End-of-file", "Keepalive", "Client",)


class LibvirtMonitor(object):

    def __init__(self):
        self.connections = []
        self.migration_monitors = {}
        self.settings = settings
        self.db_actor = db.InfluxDBActor()
        self.db_actor.start()

    def start(self):
        for uri in self.settings.LIBVIRT['URI']:
            self._start(uri)

    def _start(self, uri):
        conn = libvirt.openReadOnly(uri)
        log.info("Connecting to %s", uri)
        self.connections.append(conn)

        self._register_libvirt_callbacks(conn)

        doms_watcher_thread = watcher.LibvirtDomainsWatcher(
            conn,
            self.migration_monitors,
            self.db_actor)
        doms_watcher_thread.start()

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

        self.db_actor.tell(({
            "domain_id": dom_id,
            "domain_name": dom_name,
            "event": EVENT_STRINGS[event],
            "event_detail": EVENT_DETAILS[event][detail]},
            {"value": 1 if boundary_event else 0},
            self.settings.INFLUXDB["EVENTS_MEASUREMENT"]))

    def _conn_close_handler(self, conn, reason, opaque):
        def reconnect():
            uri = conn.getURI()
            log.debug("Reconnection %s" % (uri,))
            self.connections.remove(conn)
            self._start(uri)

        log.error("Closed connection: %s: %s",
                  conn.getURI(),
                  REASON_STRINGS[reason])
        if reason == 0:
            utils.defer(self.reconnect(),
                        seconds=self.settings.INFLUXDB["RECONNECT"])

    def stop(self):
        for dom_id in self.migration_monitors:
            dom_actor = self.migration_monitors[dom_id]
            dom_actor.stop()
            log.debug("Destroy DomJobMonitorActor for domain with id %s",
                      dom_id)

        self.db_actor.stop()
        for conn in self.connections:
            log.debug("Closing " + conn.getURI())
            conn.close()
