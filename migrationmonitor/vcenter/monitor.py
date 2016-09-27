import ssl
import time
from collections import deque
from datetime import datetime

from pyVim import connect
from pyVmomi import vmodl, vim



from migrationmonitor import settings
from migrationmonitor.common.utils import retry
from migrationmonitor.common import logger as log
from migrationmonitor.common.actor import BaseActor
from migrationmonitor.common.db import InfluxDBActor


def _is_migration_event(event):
    return isinstance(event, vim.event.VmMigratedEvent) or \
        isinstance(event, vim.event.VmBeingHotMigratedEvent)

def _create_vcenter_connection():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    log.debug("Connecting to vCenter %s", settings.VCENTER["HOST"])
    return \
        connect.SmartConnect(host=settings.VCENTER["HOST"],
                             user=settings.VCENTER["USERNAME"],
                             pwd=settings.VCENTER["PASSWORD"],
                             sslContext=ctx)

class VCenterMonitor(BaseActor):
    """Live migration events monitoring actor for VMWare vCenter
    """
    def __init__(self):
        super(VCenterMonitor, self).__init__()

        self.vc_connect = None
        self.reported_event_ids = deque(maxlen=settings.VCENTER["EVENTS_BUFFER_LENGTH"])
        self.db_actor = InfluxDBActor()


    def start(self):
        """Start the actor
        """
        self.db_actor.start()
        self.vc_connect = _create_vcenter_connection()
        super(VCenterMonitor, self).start()
        self.tell("start")


    def stop(self):
        """Release and stop all actor resources
        """
        self.db_actor.stop()
        connect.Disconnect(self.vc_connect)
        super(VCenterMonitor, self).stop()


    def _not_reported_yet(self, event_id):
        not_in_cache = True
        for reported_event_id in self.reported_event_ids:
            if event_id == reported_event_id:
                not_in_cache = False
        return not_in_cache

    def _on_receive(self, item):
        events = self._fetch_vcenter_events()
        log.debug("Got %s events from vCenter.", len(events))

        for event in events:
            event_id = event.key
            if self._not_reported_yet(event_id):
                self.reported_event_ids.append(event_id)
                tags = {"vm_name": event.vm.name,
                        "vm_id": event.vm.vm}

                values = {"value": 1}
                self.db_actor.tell((tags,
                                    values,
                                    settings.INFLUXDB["EVENTS_MEASUREMENT"],
                                    event.createdTime))

                log.info("Reported %s event to influxdb.", event_id)
                log.debug("%s %s %s",
                          event.createdTime,
                          type(event).__name__,
                          event)
            else:
                log.debug("Event: %s already reported.", event_id)


        time.sleep(settings.VCENTER["POLL_FREQ"])
        self.tell("continue")


    def _reconnect(self, tries_remaining, ex, _delay):
        log.error("Caught %s", ex)
        self.vc_connect = _create_vcenter_connection()


    @retry(max_tries=10, hook=_reconnect)
    def _fetch_vcenter_events(self):
        emgr = self.vc_connect.content.eventManager
        efspec = vim.event.EventFilterSpec()

        efespec = vim.event.EventFilterSpec.ByEntity()
        efespec.entity = self.vc_connect.content.rootFolder
        efespec.recursion = vim.event.EventFilterSpec.RecursionOption.all
        efspec.entity = efespec

        eftspec = vim.event.EventFilterSpec.ByTime()

        lower_bound = settings.VCENTER["EVENTS_HISTORY_WINDOW_LOWER_BOUND"]
        upper_bound = settings.VCENTER["EVENTS_HISTORY_WINDOW_UPPER_BOUND"]

        eftspec.beginTime = datetime.now() - lower_bound
        eftspec.endTime = datetime.now() + upper_bound
        efspec.time = eftspec

        ehc = emgr.CreateCollectorForEvents(efspec)
        ehc.SetCollectorPageSize(settings.VCENTER["EVENTS_BATCH_SIZE"])
        events = ehc.latestPage
        total = len(events)

        result = []

        while len(events) > 0:
            for _, event in enumerate(events):
                if _is_migration_event(event):
                    result.append(event)

            ehc.ResetCollector()
            events = ehc.ReadPreviousEvents(settings.VCENTER["EVENTS_BATCH_SIZE"])
            total += len(events)
            if total > settings.VCENTER["EVENTS_BATCH_SIZE"]:
                break

        return result
