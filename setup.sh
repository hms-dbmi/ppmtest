#!/bin/bash

# Check for passed AWS credentials
aws sts get-caller-identity || { echo "AWS CLI not installed or AWS credentials are not set, exiting..."; exit 1; }

# Get ECR login
eval $(aws ecr get-login --no-include-email --region us-east-1)

# Ensure we have the Selenium image
docker pull elgalu/selenium