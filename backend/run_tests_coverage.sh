#!/bin/bash
source .venv/bin/activate
python3 -m coverage run run_tests.py
RETURN_CODE=$?
python3 -m coverage report
python3 -m coverage html
python3 -m coverage xml 
deactivate
exit $RETURN_CODE
