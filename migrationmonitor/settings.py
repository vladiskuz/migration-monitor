from datetime import timedelta

DEBUG = True

PID_FILE = "/tmp/migration-monitor.pid"
LOG_FILE = "/tmp/migration-monitor.log"

LIBVIRT = {
    "URI": ["qemu:///system"],
    "POLL_FREQ": 0.1,
}

VCENTER = {
    "HOST": 'vcenter-ent2.ad.mirantis.net',
    "USERNAME": 'vsphere.local\\administrator',
    "PASSWORD": 'Ytpfvfq!1',

    "POLL_FREQ": 0.1,
    "EVENTS_BATCH_SIZE": 100,
    "EVENTS_BUFFER_LENGTH": 1000,
    "EVENTS_HISTORY_WINDOW_LOWER_BOUND": timedelta(minutes=7),
    "EVENTS_HISTORY_WINDOW_UPPER_BOUND": timedelta(minutes=1)
}

INFLUXDB = {
    "HOST": 'monit-ent.vm.mirantis.net',
    "PORT": '8086',
    "USERNAME": '',
    "PASSWORD": '',
    "DATABASE": 'vcenter_dev',
    "EVENTS_MEASUREMENT": 'events',
    "JOBINFO_MEASUREMENT": 'jobinfo',
    "RECONNECT": 10,  # sec

    "TAGS": {
        "scenario": "",
        "run": "",
    }
}
