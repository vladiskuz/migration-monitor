import sys
import time

from daemonize import Daemonize

import logger as log
import monitor
import settings
import utils


def main():
    utils.start_event_loop()
    libvirt_monitor = monitor.LibvirtMonitor()
    libvirt_monitor.start()

    old_exitfunc = getattr(sys, 'exitfunc', None)

    def exitfunc():
        log.info("Shutting down.")
        libvirt_monitor.stop()
        if old_exitfunc:
            old_exitfunc()

    sys.exitfunc = exitfunc

    while True:
        time.sleep(1)


if __name__ == "__main__":
    if getattr(settings, 'DEBUG', False):
        main()
    else:
        daemon = Daemonize(app="migration_monitor",
                           pid=settings.PID_FILE,
                           action=main,
                           keep_fds=[log.handler.stream.fileno()])
        daemon.start()
