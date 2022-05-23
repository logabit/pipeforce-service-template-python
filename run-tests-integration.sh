#!/bin/bash

# Run integration tests only and print final test results
pytest -k 'test_integration_' --junitxml result.xml >> /dev/null; cat result.xml