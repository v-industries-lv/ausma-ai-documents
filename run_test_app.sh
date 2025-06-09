#!/bin/bash
source .venv/bin/activate
python3 flask_app.py --test-delay-seconds 5
deactivate