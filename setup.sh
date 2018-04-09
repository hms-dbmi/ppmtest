#!/bin/bash

# Check for passed AWS credentials
if [ -z ${AWS_ACCESS_KEY_ID+x} ] && [ -z ${AWS_SECRET_ACCESS_KEY+x} ]; then
    echo "AWS credentials are not set, exiting..."
    exit 1
fi

# Install aws-cli
pip install --upgrade awscli

# Get ECR login
eval $(aws ecr get-login --no-include-email --region us-east-1)

# Check for docker-compose
if ! [ -x "$(command -v docker-compose)" ]; then
  echo "docker-compose not installed"

  # Install it
  sudo curl -L https://github.com/docker/compose/releases/download/1.20.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose

  # Test it
  if docker-compose --version ; then
    echo "docker-compose installed!"
  else
    echo 'Error: docker-compose is not installed' >&2
    exit 1
  fi
fi

# Ensure we have the Selenium image
docker pull elgalu/selenium