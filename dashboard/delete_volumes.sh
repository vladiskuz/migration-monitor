#!/bin/bash

source .env

echo "Start deleting volumes:"
docker volume rm ${influx_name} ${grafana_name}
