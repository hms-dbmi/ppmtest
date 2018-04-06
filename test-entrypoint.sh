#!/bin/bash

# Install pip requirements
pip install -r /requirements.txt

# Run the command
exec "$@"