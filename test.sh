#!/bin/bash

# Check for a specific test
export PPM_TEST_TEST="$1"

# Get the latest and greatest
docker-compose pull --parallel

# Ensure the stack is not already running
docker-compose down -v --remove-orphans
docker-compose rm -v -f -s

# Output link to monitoring
echo "Follow tests at: http://localhost:4444/grid/admin/live#"

# RGet the current date and create a directory for collecting logs
today=`date +%Y%m%d_%H%M%S`
mkdir -p "./$today"

# Create a directory for collecting videos upon test failures
mkdir -p videos

# Run the stack and get exit code from tests (videos not exporting)
docker-compose up --exit-code-from test --abort-on-container-exit  2>&1 | tee "$today/test-output-$today.log"
RESULT=$?

if [ $RESULT -ne 0 ]; then

    echo 'Error: Tests failed!' >&2

    # Collect files
    docker-compose logs -t > "$today/test-logs-$today.log"
    find videos -name "*.mp4" -exec mv "{}" "$today" \;

    # Tar the output directory
    tar czf "$PPM_TEST_OUTPUT_PATH" "$today"

else

    echo "Tests succeeded!"

    # Clean up files
    rm -rf videos
    rm -rf "$today"

fi

# Clean up
docker-compose down -v --remove-orphans
docker-compose rm -v -f -s

exit $RESULT