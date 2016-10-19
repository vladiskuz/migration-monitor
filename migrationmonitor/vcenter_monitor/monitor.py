import ssl
import time
from collections import deque
from datetime import datetime

from pyVmomi import vim
from pyVim import connect as vcenter_connect

import migrationmonitor.settings
from migrationmonitor.common import actor
from migrationmonitor.common import logger as log
from migrationmonitor.common import reporter
from migrationmonitor.common.utils import retry


def _is_migration_event(event):
    return isinstance(event, vim.event.VmMigratedEvent) or \
        isinstance(event, vim.event.VmBeingHotMigratedEvent)


def _create_vcenter_connection():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    log.debug(
        "Connecting to vCenter %s",
        migrationmonitor.settings.VCENTER["HOST"])

    connection = vcenter_connect.SmartConnect(
        host=migrationmonitor.settings.VCENTER["HOST"],
        user=migrationmonitor.settings.VCENTER["USERNAME"],
        pwd=migrationmonitor.settings.VCENTER["PASSWORD"],
        sslContext=context)

    return connection


class VCenterMonitor(actor.BaseActor):
    """Live migration events monitoring actor for VMWare vCenter"""

    def __init__(self):
        super(VCenterMonitor, self).__init__()

        self.settings = migrationmonitor.settings
        self.vc_connect = None
        self.reported_event_ids = deque(
            maxlen=self.settings.VCENTER["EVENTS_BUFFER_LENGTH"])
        self.reporter = reporter.Reporter()

    def start(self):
        """Start the actor
        """
        self.reporter.start()
        self.vc_connect = _create_vcenter_connection()
        super(VCenterMonitor, self).start()
        self.tell("start")

    def stop(self):
        """Release and stop all actor resources"""

        self.reporter.stop()
        vcenter_connect.Disconnect(self.vc_connect)
        super(VCenterMonitor, self).stop()

    def _on_receive(self, item):
        events = self._fetch_vcenter_events()
        log.debug("Got %s events from vCenter.", len(events))

        for event in events:
            event_id = event.key
            if event_id not in self.reported_event_ids:
                self.reported_event_ids.append(event_id)
                tags = {"vm_name": event.vm.name,
                        "vm_id": event.vm.vm}

                values = {"value": 1}
                self.reporter.tell({
                    "tags": tags,
                    "values": values,
                    "measurement":
                        self.settings.MEASUREMENT["EVENTS_MEASUREMENT"],
                    "datetime": event.createdTime})

                log.debug("%s %s %s",
                          event.createdTime,
                          type(event).__name__,
                          event)
            else:
                log.debug("Event: %s already reported.", event_id)

        time.sleep(self.settings.VCENTER["POLL_FREQ"])
        self.tell("continue")

    def _reconnect(self, tries_remaining, ex, _delay):
        log.error("Caught %s", ex)
        self.vc_connect = _create_vcenter_connection()

    @retry(max_tries=10, hook=_reconnect)
    def _fetch_vcenter_events(self):
        event_filter_spec = vim.event.EventFilterSpec()

        event_filter_spec_e = vim.event.EventFilterSpec.ByEntity()
        event_filter_spec_e.entity = self.vc_connect.content.rootFolder
        event_filter_spec_e.recursion = \
            vim.event.EventFilterSpec.RecursionOption.all
        event_filter_spec.entity = event_filter_spec_e

        event_filter_spec_t = vim.event.EventFilterSpec.ByTime()

        lower_bound = \
            self.settings.VCENTER["EVENTS_HISTORY_WINDOW_LOWER_BOUND"]
        upper_bound = \
            self.settings.VCENTER["EVENTS_HISTORY_WINDOW_UPPER_BOUND"]

        time_now = datetime.now()
        event_filter_spec_t.beginTime = time_now - lower_bound
        event_filter_spec_t.endTime = time_now + upper_bound
        event_filter_spec.time = event_filter_spec_t

        event_manager = self.vc_connect.content.eventManager
        event_collector = event_manager.CreateCollectorForEvents(
            event_filter_spec)
        event_collector.SetCollectorPageSize(
            self.settings.VCENTER["EVENTS_BATCH_SIZE"])
        events = event_collector.latestPage
        total = len(events)

        result = []
        batch_size = self.settings.VCENTER["EVENTS_BATCH_SIZE"]
        while len(events) > 0:
            for _, event in enumerate(events):
                if _is_migration_event(event):
                    result.append(event)

            event_collector.ResetCollector()
            events = event_collector.ReadPreviousEvents(batch_size)
            total += len(events)
            if total > batch_size:
                break

        return result
