#!/bin/bash

chmod 755 /app/trigger.sh

while ! nc -z api 5000; do
  echo "Waiting for API to be available..."
  sleep 2
done
# Trigger the integration endpoint
curl -X GET http://api:5000/integration

# Post new tickets from the JSON file
curl -X POST --location 'http://api:5000/new_tickets' --header 'Content-Type: application/json' --data-binary '@backend/seeds/new_tickets.json'

# Trigger the recalculation of metrics
curl -X GET http://api:5000/recalculate_metrics