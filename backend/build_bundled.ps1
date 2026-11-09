Remove-Item -Recurse dist -ErrorAction SilentlyContinue

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements_windows.txt
pip install -r requirements-build.txt

pyinstaller -y `
    --collect-all engineio `
    --hidden-import socketio --hidden-import flask_socketio --hidden-import threading --hidden-import time --hidden-import queue `
    --collect-all chromadb flask_app.py

deactivate
