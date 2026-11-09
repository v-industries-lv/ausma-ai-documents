rmdir /s /q dist

python -m venv .venv

dir /A:H /S /B .venv

.venv\Scripts\activate.bat

pip install -r requirements.txt
pip install -r requirements_windows.txt
pip install -r requirements-build.txt

pyinstaller -y ^
    --collect-all engineio ^
    --hidden-import socketio --hidden-import flask_socketio --hidden-import threading --hidden-import time --hidden-import queue ^
    --collect-all chromadb flask_app.py

deactivate
