#!/bin/bash

# Bring the stack down
docker-compose down -v --remove-orphans
docker-compose rm -v -f -s