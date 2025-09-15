#!/bin/bash
source .venv/bin/activate
python3 flask_app.py --production "$@"
deactivate