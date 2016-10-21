#!/bin/bash

source .env

echo "Stop containers:"
docker stop ${influx_name} ${grafana_name}

echo "Delete containers:"
docker rm ${influx_name} ${grafana_name}

echo "Delete networks:"
docker network rm ${network}
