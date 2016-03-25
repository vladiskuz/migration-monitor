import sys
import time
import settings
from daemonize import Daemonize
from logger import info, handler as fh
from monitor import monitor_libvirt_events
from util import start_event_loop


def main():
    start_event_loop()
    disposer = monitor_libvirt_events(settings.LIBVIRT,
                                      settings.INFLUXDB)

    info("Connecting to %s" % (", ".join(settings.LIBVIRT["URI"])))

    old_exitfunc = getattr(sys, 'exitfunc', None)

    def exitfunc():
        info("Shutting down.")
        disposer()
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
                           keep_fds=[fh.stream.fileno()])
        daemon.start()
