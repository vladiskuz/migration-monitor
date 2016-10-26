#!/bin/bash -e

source .env

network_id=$(docker network create ${network})
echo "Created network id: $network_id"

influx_id=$(docker run -d -p 8083:8083 -p 8086:8086 -v ${influx_name}:/var/lib/influxdb -v /etc/localtime:/etc/localtime:ro --net ${network} --name ${influx_name} influxdb:0.13-alpine)
echo "Created InfluxDB container id: $influx_id"

grafana_id=$(docker run -d -p 3000:3000 -v ${grafana_name}:/var/lib/grafana -v /etc/localtime:/etc/localtime:ro --net ${network} --name ${grafana_name} grafana/grafana)
echo "Created Grafana container id: $grafana_id"
