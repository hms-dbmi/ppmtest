PPM Tests
=========

*A program for running the PPM integration tests*


## Purpose

Run Selenium integration tests on the PPM suite

## Instructions

0. Ensure valid AWS credentials are configured for the environment

1. Run the `test.sh [AWS_ACCESS_KEY_ID] [AWS_SECRET_ACCESS_KEY] [tests]` script to build the stack and start tests

n. Visit `http://localhost:4444/grid/admin/live#` for monitoring tests

n. The command runs and returns `0` for successful tests and `1` for failed tests

n. Videos are record of tests so in the event of failure, check the `videos/` directory for details