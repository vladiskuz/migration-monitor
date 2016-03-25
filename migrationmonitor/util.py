import threading

import libvirt


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
