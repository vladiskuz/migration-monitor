import threading
import libvirt


def run_native_event_loop():
    """Runs native libvirt event loop
    """
    while True:
        libvirt.virEventRunDefaultImpl()

EVENT_LOOP_THREAD = None
def start_event_loop():
    """Defines eventLoopThread global and starts the thread
    """
    global EVENT_LOOP_THREAD
    libvirt.virEventRegisterDefaultImpl()
    EVENT_LOOP_THREAD = threading.Thread(target=run_native_event_loop,
                                         name="libvirtEventLoop")
    EVENT_LOOP_THREAD.setDaemon(True)
    EVENT_LOOP_THREAD.start()


def get_dom_name_by_id(conn, dom_id):
    """Shortcut for getting libvirt domain name by ID
    """
    dom = conn.lookupByID(dom_id)
    return dom.name()
