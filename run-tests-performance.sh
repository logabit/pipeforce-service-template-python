#!/bin/bash

# Run performance tests only and print final test results
pytest -k 'test_performance_' --junitxml result.xml >> /dev/null; cat result.xml