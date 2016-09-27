import threading
import libvirt


def run_native_event_loop():
    """Runs native libvirt event loop"""

    while True:
        libvirt.virEventRunDefaultImpl()

event_loop_thread = None


def start_event_loop():
    """Defines eventLoopThread global and starts the thread"""

    global event_loop_thread
    libvirt.virEventRegisterDefaultImpl()
    event_loop_thread = threading.Thread(target=run_native_event_loop,
                                         name="libvirtEventLoop")
    event_loop_thread.setDaemon(True)
    event_loop_thread.start()


def get_dom_name_by_id(conn, dom_id):
    """Shortcut for getting libvirt domain name by ID
    """
    dom = conn.lookupByID(dom_id)
    return dom.name()
