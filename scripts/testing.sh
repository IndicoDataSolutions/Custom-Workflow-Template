#!/bin/bash
wait_dependencies rabbitmq
pytest -v -m "not api_call"
