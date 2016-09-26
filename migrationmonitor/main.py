import sys
import time

from daemonize import Daemonize

from migrationmonitor.common import logger as log
from migrationmonitor.libvirt.monitor import LibvirtMonitor
from vcenter.monitor import VCenterMonitor
import migrationmonitor.settings


def main():
    monitor = VCenterMonitor()
    monitor.start()

    old_exitfunc = getattr(sys, 'exitfunc', None)


    def exitfunc():
        log.info("Shutting down.")
        monitor.stop()
        if old_exitfunc:
            old_exitfunc()

    sys.exitfunc = exitfunc

    while True:
        time.sleep(1)

    if getattr(settings, 'DEBUG', False):
        main()
    else:
        daemon = Daemonize(app="migration_monitor",
                           pid=settings.PID_FILE,
                           action=main,
                           keep_fds=[log.handler.stream.fileno()])
        daemon.start()

