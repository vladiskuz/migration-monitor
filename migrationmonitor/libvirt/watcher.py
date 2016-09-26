import time
import threading
from Queue import Queue

import libvirt

import migrationmonitor.settings
from migrationmonitor.libvirt.libvirt_utils import get_dom_name_by_id

from migrationmonitor.common import actor
from migrationmonitor.common import logger as log


class LibvirtDomainsWatcher(threading.Thread):
    """Search for new and disappeared (deleted or migrated) domains.
    If a new domain is found it will be added to a queue for further
    handling.
    """

    def __init__(self, conn, migration_monitors, db_actor, interval=0.15):
        super(LibvirtDomainsWatcher, self).__init__()
        self.daemon = True

        self.conn = conn
        self.interval = interval
        self.migration_monitors = migration_monitors
        self.db_actor = db_actor

        self.doms_job_monitor = DomainsJobMonitorActorCreator(
            conn,
            self.migration_monitors,
            self.db_actor)
        self.doms_job_monitor.start()

    def run(self):
        known_dom_ids = set()
        lost_dom_ids = set()

        while True:
            current_dom_ids = self.conn.listDomainsID()
            new_dom_ids = set(current_dom_ids) - known_dom_ids
            lost_dom_ids = known_dom_ids - set(current_dom_ids)

            for dom_id in new_dom_ids:
                self.doms_job_monitor.tell(('start_dom_monitoring', dom_id))
                known_dom_ids.add(dom_id)
                log.info(
                    "Domain: (%s)%s has found on %s",
                    dom_id,
                    get_dom_name_by_id(self.conn, dom_id),
                    self.conn.getURI())

            for dom_id in lost_dom_ids:
                known_dom_ids.remove(dom_id)
                log.info(
                    "Domain with id %s was not found on %s",
                    dom_id,
                    self.conn.getURI())

            time.sleep(self.interval)


class DomainsJobMonitorActorCreator(actor.BaseActor):
    """Factory which gets new domain from a queue and creates a domain actor
    that will tracks libvirt job stats about the particular domain.
    """

    def __init__(self, conn, migration_monitors, db_actor):
        super(DomainsJobMonitorActorCreator, self).__init__()
        self.daemon = True
        self.conn = conn
        self.migration_monitors = migration_monitors
        self.db_actor = db_actor

    def _on_receive(self, msg):
        cmd, dom_id = msg
        dom_name = get_dom_name_by_id(self.conn, dom_id)

        dom_actor = DomainJobMonitorActor(
            self.conn,
            dom_id,
            self.migration_monitors,
            self.db_actor)
        self.migration_monitors[dom_id] = dom_actor
        dom_actor.start()
        dom_actor.tell(('start_job_monitoring', dom_id))

        log.info(
            "Start job monitoring for domain (%s)%s on %s",
            dom_id,
            get_dom_name_by_id(self.conn, dom_id),
            self.conn.getURI())


class DomainJobMonitorActor(actor.BaseActor):
    """Gets domain job stats and put it into database.
    """

    def __init__(self, conn, dom_id, migration_monitors, db_actor):
        super(DomainJobMonitorActor, self).__init__()
        self.conn = conn
        self.dom_id = dom_id
        self.settings = migrationmonitor.settings
        self.migration_monitors = migration_monitors
        self.db_actor = db_actor

    def _on_receive(self, msg):
        _, dom_id = msg
        try:
            dom = self.conn.lookupByID(self.dom_id)
            job_info = dom.jobStats()
            log.debug("jobStats: {0}".format(job_info))
            self.db_actor.tell(({"domain_id": self.dom_id,
                                 "domain_name": dom.name()},
                                job_info,
                                self.settings.INFLUXDB["JOBINFO_MEASUREMENT"]))

            time.sleep(self.settings.LIBVIRT["POLL_FREQ"])
            self.tell(("continue", dom_id))

        except libvirt.libvirtError:
            self.stop()
            log.debug("Destroy DomJobMonitorActor for domain with id %s",
                      self.dom_id)
            del self.migration_monitors[self.dom_id]
