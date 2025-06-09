#!/bin/bash
source .venv/bin/activate
python3 flask_app.py --production --embedding-model "bge-m3"
deactivate