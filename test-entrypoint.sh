#!/bin/bash

# Install pip requirements
pip install -r /requirements.txt

# Run the command
nose2 -s /tests $PPM_TEST_TEST
RESULT=$?

# Figure out a better way to ensure videos were exported
while [ ! -f /videos/*.mp4 ]; do
    echo "Waiting on video..."
    sleep 3
done

# Give them time to save
sleep 10

exit $RESULT