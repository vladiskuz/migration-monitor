#!/bin/bash -e

source .env

docker network create ${network}
docker run -d -v grafana:/var/lib/grafana -p 3000:3000 --net ${network} --name ${grafana_name} grafana/grafana
docker run -d -p 8083:8083 -p 8086:8086 -v influxdb:/var/lib/influxdb --net ${network} --name ${influx_name} influxdb:0.13-alpine

