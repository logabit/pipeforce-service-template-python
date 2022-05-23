#!/bin/bash

# Run all tests and print final test results
pytest --junitxml result.xml >> /dev/null; cat result.xml