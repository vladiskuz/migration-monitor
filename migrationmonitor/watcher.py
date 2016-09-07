from Queue import Queue
import time

import libvirt

import actor
import db
import logger as log
import settings
import threading
import utils


class DomsWatcher(threading.Thread):
    """Search for new and disappeared (deleted or migrated) domains.
    If a new domain is found it will be added to a queue for further
    handling.
    """
    
    def __init__(self, conn, migration_monitors, interval=0.15):
        super(DomsWatcher, self).__init__()
        self.daemon = True

        self.conn = conn
        self.interval = interval
        self.migration_monitors = migration_monitors

        self.new_dom_ids_q = Queue()

        doms_job_monitor_thread = DomsJobMonitorActorCreator(
            conn,
            self.new_dom_ids_q,
            self.migration_monitors)
        doms_job_monitor_thread.start()

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
                known_dom_ids.remove(dom_id)
                log.info(
                    "Domain with id %s was not found on %s",
                    dom_id,
                    self.conn.getURI())

            time.sleep(self.interval)


class DomsJobMonitorActorCreator(threading.Thread):
    """Factory which gets new domain from a queue and creates a domain actor
    that will track libvirt job stats about the particular domain.
    """

    def __init__(self, conn, new_dom_ids_q, migration_monitors, interval=0.15):
        super(DomsJobMonitorActorCreator, self).__init__()
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

                dom_actor = DomJobMonitorActor(
                    self.conn,
                    dom_id,
                    self.migration_monitors)
                self.migration_monitors[dom_id] = dom_actor
                dom_actor.start()
                dom_actor.add_task_to_queue(('start_job_monitoring', dom_id))

                log.info(
                    "Start job monitoring for domain (%s)%s on %s",
                    dom_id,
                    utils.get_dom_name_by_id(self.conn, dom_id),
                    self.conn.getURI())
                self.new_dom_ids_q.task_done()

            time.sleep(self.interval)


class DomJobMonitorActor(actor.BaseActor):
    """Gets domain job stats and put it into database.
    """

    def __init__(self, conn, dom_id, migration_monitors):
        super(DomJobMonitorActor, self).__init__()
        self.conn = conn
        self.dom_id = dom_id
        self.settings = settings
        self.migration_monitors = migration_monitors

    def _run(self, msg):
        cmd, dom_id = msg
        try:
            dom = self.conn.lookupByID(self.dom_id)
            job_info = dom.jobStats()
            log.debug("jobStats: {0}".format(job_info))
            db.write(({
                "domain_id": self.dom_id,
                "domain_name": dom.name()},
                job_info,
                self.settings.INFLUXDB["JOBINFO_MEASUREMENT"]))

            time.sleep(self.settings.LIBVIRT["POLL_FREQ"])
            self.add_task_to_queue(("continue", dom_id))

        except libvirt.libvirtError as ex:
            self.stop()
            log.debug("Destroy DomJobMonitorActor for domain with id %s",
                      self.dom_id)
            del self.migration_monitors[self.dom_id]
