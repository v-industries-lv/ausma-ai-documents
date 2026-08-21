#!/bin/bash
source .venv/bin/activate
python3 run_tests.py
RETURN_CODE=$?
deactivate
exit $RETURN_CODE