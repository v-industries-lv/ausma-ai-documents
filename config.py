from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
import logging
from settings import Settings

RAG_DOCUMENT_COUNT = 10
RAG_DOCUMENT_TOKEN_LEN = 1000
COOKIE_USERNAME = 'username'

class KBServiceStatusFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return not ('/kb_service/status' in msg and ' 200 ' in msg)

def setup_app():
    app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

    app.config['SECRET_KEY'] = ''
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    socketio = SocketIO(app)
    return app, db, socketio

app, db, socketio = setup_app()

# Filter out request spam
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(KBServiceStatusFilter())
settings = Settings()