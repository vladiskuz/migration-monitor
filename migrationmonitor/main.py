import sys
import time

from daemonize import Daemonize

from migrationmonitor import settings
from migrationmonitor.common import logger as log
from migrationmonitor.libvirt.monitor import LibvirtMonitor
from migrationmonitor.vcenter.monitor import VCenterMonitor


def create_monitor(provider):
    if provider is "LIBVIRT":
        return LibvirtMonitor()
    elif provider is "VCENTER":
        return VCenterMonitor()
    else:
        raise NotImplementedError


def main():
    monitor = create_monitor(settings.PROVIDER)
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

if __name__ == "__main__":
    if getattr(settings, 'DEBUG', False):
        main()
    else:
        daemon = Daemonize(app="migration_monitor",
                           pid=settings.PID_FILE,
                           action=main,
                           keep_fds=[log.handler.stream.fileno()])
        daemon.start()
