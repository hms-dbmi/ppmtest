PPM Tests
=========

*A program for running the PPM integration tests*


## Purpose

Run Selenium integration tests on the PPM suite

## Instructions

0. Ensure valid AWS credentials are configured for the environment

1. Run `setup.sh` to ensure all dependencies and environments are installed and configured

2. Run `build.sh app1,app2,app3` for the apps to test. This will build the app's Docker image from source and use
that in the test stack

3. Run the `test.sh [tests]` script to build the stack and start tests. If nothing is passed for `test` all tests found
in the context will be run.

4. Visit `http://localhost:4444/grid/admin/live#` for monitoring tests

5. The command runs and returns `0` for successful tests and `1` for failed tests

6. Videos are record of tests so in the event of failure, check the `videos/` directory for details