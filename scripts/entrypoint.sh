#!/bin/bash
wait_dependencies rabbitmq
echo "Started Container" > /var/log/verbose-custom_app.log &
tail -Fq /var/log/verbose-custom_app.log
