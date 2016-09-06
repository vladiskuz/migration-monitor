DEBUG = True

PID_FILE = "/tmp/migration-monitor.pid"
LOG_FILE = "/tmp/migration-monitor.log"

LIBVIRT = {
    "URI": ["qemu:///system"],
    "POLL_FREQ": 0.1,
}

INFLUXDB = {
    "HOST": '172.18.66.94',
    "PORT": '8086',
    "USERNAME": '',
    "PASSWORD": '',
    "DATABASE": 'openstack',
    "EVENTS_MEASUREMENT": 'libvirt_events',
    "JOBINFO_MEASUREMENT": 'libvirt_jobinfo',
    "RECONNECT": 10,  # sec
    
    "TAGS": {
        "scenario": "",
        "run": "",
    }
}
