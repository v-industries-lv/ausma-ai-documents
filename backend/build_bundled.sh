#!/bin/bash -xe
rm -r dist || true

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_linux.txt
pip install -r requirements-build.txt
pyinstaller -y \
 --collect-all engineio --hidden-import socketio --hidden-import flask_socketio --hidden-import threading --hidden-import time --hidden-import queue \
 --collect-all chromadb \
 flask_app.py
deactivate