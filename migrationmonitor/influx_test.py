import sys
import time

from datetime import datetime as dt, timedelta
from influxdb import InfluxDBClient
from settings import INFLUXDB as influx_settings


client = InfluxDBClient(influx_settings["HOST"],
                        influx_settings["PORT"],
                        influx_settings["USERNAME"],
                        influx_settings["PASSWORD"],
                        "influx_test")

def write_to_db(past=None, future=None):
    timestamp = dt.now()
    if past is not None:
        timestamp = timestamp - timedelta(seconds=past)
    elif future is not None:
        timestamp = timestamp + timedelta(seconds=future)
    
    print "Writing with timestamp: %s" % (timestamp)

    json_body = [{
        "time": int(time.time() * 1000000) * 1000,
        "measurement": "test_measurement",
        "tags": {
            "test_tag": "foo"
        },
        "fields": {
            "value": 1
        }
    }]
    client.write_points(json_body)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def test_case(fn):
    def wrapper_fn():
        print bcolors.OKGREEN + "Test case: " + bcolors.ENDC + fn.__name__.replace("_", " ")

        fn()
        result = {}
        iterations = 0

        sys.stdout.write("Waiting for query result")
        sys.stdout.flush()

        while len(result) == 0 and iterations <= 100:
            result = client.query("select value from test_measurement;")
            time.sleep(0.1)
            if iterations % 10 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            iterations += 1
        
        if len(result) == 0:
            print "NO LUCK"    
        else:
            print "Result is: %s" % (result,)
        
        client.query('drop measurement test_measurement')
        print ""

    return wrapper_fn

import subprocess
sys.stdout.write("Server time:\t")
sys.stdout.flush()

subprocess.Popen('ssh vnykytiuk@monit-ent.vm.mirantis.net "date +%s"', shell=True)

time.sleep(3)
print "Local time:\t%s" % (int(time.time()),)

@test_case
def test_influx_write_in_the_past():
    write_to_db(past=1000)


@test_case
def test_influx_write_normal():
    write_to_db()


@test_case
def test_influx_write_in_the_future():
    write_to_db(future=1000)

test_influx_write_in_the_past()
test_influx_write_normal()
test_influx_write_in_the_future()