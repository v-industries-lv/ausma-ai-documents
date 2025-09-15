#!/bin/bash -xe
rm -r dist || true
source .venv/bin/activate
pyinstaller -y --add-data "flask-resources:flask-resources" --add-data "static:static" \
 --collect-all engineio --hidden-import socketio --hidden-import flask_socketio --hidden-import threading --hidden-import time --hidden-import queue \
 --collect-all chromadb \
 flask_app.py
deactivate

npm run build