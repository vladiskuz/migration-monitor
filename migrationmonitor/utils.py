import threading

import libvirt

from actor import POISON_PILL
import logger as log


def run_native_event_loop():
    while True:
        libvirt.virEventRunDefaultImpl()


def start_event_loop():
    global eventLoopThread
    libvirt.virEventRegisterDefaultImpl()
    eventLoopThread = threading.Thread(
            target=run_native_event_loop, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def defer(fn, seconds):
    threading.Timer(seconds, fn).start()

def get_dom_name_by_id(conn, dom_id):
    dom = conn.lookupByID(dom_id)
    return dom.name()

def kill_dom_job_monitor_actor(migration_monitors, dom_id):
        migration_monitors[dom_id](POISON_PILL)
        log.debug(
            "Sending poison pill to monitoring process for domain: %s",
            dom_id)
