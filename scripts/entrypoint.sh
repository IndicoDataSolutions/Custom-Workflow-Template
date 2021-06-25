#!/bin/bash
wait_dependencies rabbitmq
echo "Started Container" > /var/log/verbose-corelogic.log &
tail -Fq /var/log/verbose-corelogic.log
