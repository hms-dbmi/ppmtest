#!/bin/bash

# Get the latest and greatest
docker-compose pull --parallel

# Output link to monitoring
echo "Follow tests at: http://18.204.95.224:4444/grid/admin/live#"

# Export the test
export PPM_TEST_TEST=$1

# Run the stack and get exit code from tests (videos not exporting)
docker-compose up --exit-code-from test --abort-on-container-exit
RESULT=$?

if [ $RESULT -ne 0 ]; then

    echo 'Error: Tests failed!' >&2

else

    echo "Tests succeeded!"

fi

exit $RESULT