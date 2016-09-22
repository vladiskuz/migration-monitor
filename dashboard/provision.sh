#!/bin/bash

source .env

curl -s -X POST "${influx_local_url}/query" --data-urlencode "q=CREATE DATABASE ${database}"
echo "."

curl -s -X POST \
  "${grafana_url}/api/datasources" \
  --header "Content-Type:application/json" \
  --data "{\"Access\":\"direct\",\"basicAuth\":false,\"basicAuthPassword\":\"\",\"basicAuthUser\":\"\",\"database\":\"${database}\",\"id\":8,\"isDefault\":false,\"jsonData\":null,\"Name\":\"LV\",\"orgId\":1,\"Type\":\"influxdb\",\"url\":\"${influx_internal_docker_url}\",\"withCredentials\":false}"
echo "."

curl -s -X POST \
  "${grafana_url}/api/dashboards/db" \
  --header "Content-Type:application/json" \
  --data @dashboard.json
echo "."

