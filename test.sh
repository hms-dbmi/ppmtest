#!/bin/bash

function cleanup() {
    # Bring the stack down and purge everything
    docker-compose down -v --remove-orphans
    docker-compose rm -v -f -s
}

# Manage AWS credentials
export AWS_ACCESS_KEY_ID="$1"
export AWS_SECRET_ACCESS_KEY="$2"
export PPM_TEST_TEST="$3"

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

# Get the latest and greatest
docker-compose pull --parallel

# Ensure the stack is not already running
cleanup

# Run the tests
today=`date +%Y%m%d_%H%M%S`
docker-compose up --exit-code-from test --abort-on-container-exit &>test-output-$today.log
RESULT=$?

# Get logs
docker-compose logs -t > test-logs-$today.log

# Clean up
cleanup

if [ $RESULT -ne 0 ]; then

    echo 'Error: Tests failed!' >&2

    # Collect files
    mkdir -p "./$today"
    find videos -name "*.mp4" -exec mv "{}" "$today" \;
    find . -name "*.log" -exec mv "{}" "$today" \;

fi

exit $RESULT