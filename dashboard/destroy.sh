#!/bin/bash

source .env

docker stop ${influx_name} ${grafana_name}
docker rm ${influx_name} ${grafana_name}
docker network rm ${network}
