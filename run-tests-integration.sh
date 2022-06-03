#!/bin/bash

# Run integration tests (includes unit tests) and print final test results
pytest -k 'not test_performance_' --junitxml result.xml >> /dev/null; cat result.xml