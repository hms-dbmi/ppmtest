#!/bin/bash

# Check for a specific test
export PPM_TEST_TEST="$1"

# Get the output archive path
ARTIFACTS_PATH=${PPM_TEST_ARTIFACTS:-artifacts}

# RGet the current date and create a directory for collecting logs
today=`date +%Y%m%d_%H%M%S`
mkdir -p "./$ARTIFACTS_PATH"

# Determine what to call the stack
PPM_PROJECT_NAME=${PPM_TEST_STACK:-$today}

# Get the latest and greatest
docker-compose -p $PPM_PROJECT_NAME pull --parallel

# Ensure the stack is not already running
docker-compose -p $PPM_PROJECT_NAME down -v --remove-orphans
docker-compose -p $PPM_PROJECT_NAME rm -v -f -s

# Output link to monitoring
echo "Follow tests at: http://18.204.95.224:4444/grid/admin/live#"

# Run the stack and get exit code from tests (videos not exporting)
docker-compose -p $PPM_PROJECT_NAME up --exit-code-from test --abort-on-container-exit | tee "./$ARTIFACTS_PATH/test-output-$today.log"
RESULT=${PIPESTATUS[0]}

# Collect files
docker-compose -p $PPM_PROJECT_NAME logs -t > "$ARTIFACTS_PATH/test-logs-$today.log"

if [ $RESULT -ne 0 ]; then

    echo 'Error: Tests failed!' >&2

else

    echo "Tests succeeded!"

fi

exit $RESULT