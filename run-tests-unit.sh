#!/bin/bash

# Run unit tests only and print final test results
pytest -k 'not test_integration_' --junitxml result.xml >> /dev/null; cat result.xml