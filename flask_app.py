import argparse
import datetime
import json
import logging
import os
import time
import uuid
from typing import Optional
import requests

import markdown
import nh3
import ollama
from flask import Flask, request, render_template, session, make_response, abort, Response, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from markupsafe import escape

parser = argparse.ArgumentParser()
parser.add_argument('--production', action='store_true', help='Use production config.')
parser.add_argument('--embedding-model', type=str, help='RAG model used for retrieval.')
parser.add_argument('--test-delay-seconds', type=int, help='Test response delay in seconds.')
parser.add_argument('--custom-vectorstore', help='Specify chroma db path')
args = parser.parse_args()

RAG_DOCUMENT_COUNT = 10
RAG_DOCUMENT_TOKEN_LEN = 1000
EMBEDDING_TEMPERATURE = 0.7
LLM_NUM_PREDICT = 4096
RANDOM_SEED = 42
EMBEDDING_MODEL = args.embedding_model

# App setup
app = Flask(__name__, template_folder="flask-resources/templates", static_folder='static')

app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistant_rooms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

socketio = SocketIO(app)

# Constants
COOKIE_USER_ID = 'user_id'
COOKIE_USERNAME = 'username'

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'llm_requests.log')


class ChatRoom(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean, unique=False, default=True)
    def as_dict(self):
        return {"id": self.id, "name": self.name, "created": self.created_at.strftime("%Y-%m-%d_%H:%M:%S")}


class Users(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class RoomMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(64), db.ForeignKey('chat_room.id'))
    username = db.Column(db.String(64))  # or anonymous
    role = db.Column(db.String(16))  # 'user'/'assistant'
    content = db.Column(db.Text)
    rag_sources = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def as_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "username": self.username,
            "role": self.role,
            "content": markdown.markdown(nh3.clean(self.content)),
            "rag_sources": self.rag_sources,
            "timestamp": self.timestamp.isoformat(),
        }

def get_ollama_model_list():
    completion_models = []
    for model in [x.model for x in ollama.list().models]:
        model_info = json.loads(
            requests.post(
                'http://localhost:11434/api/show',
                data='{"model": "' + model + '"}',
                headers={'Content-Type': 'application/json'}
            ).content
        )
        if 'completion' in model_info['capabilities']:
            completion_models.append(model)
    return completion_models


def logger_setup():
    global logger
    # TODO rolling format logger
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger('llm_logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_or_set_user_id():
    # Check for concurrency issues later
    user_id = request.cookies.get(COOKIE_USER_ID)
    if not user_id:
        user_id = uuid.uuid4().hex
        user_item = Users(id=user_id, name=user_id[:4])
        db.session.add(user_item)
        db.session.commit()
    return user_id


def log_llm_request(log_data, role):
    user_id = session.get('user_id')
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        payload = json.dumps(log_data)
    except Exception as e:
        payload = '"BAD_LOG_PAYLOAD"'

    entry = f"[LLM_REQUEST]_{user_id}_{timestamp}_{role}_{payload}"
    logger.info(entry)


def ollama_chat(inputs, room_id, username, history=None):
    if history is None:
        history = []
    try:
        llm_model = inputs.get('llm_model', None)
        if llm_model not in [x.model for x in ollama.list().models]:
            print(inputs)
            raise ValueError(
                f"Model {repr(llm_model)} not installed! Available models: {';'.join([x.model for x in ollama.list().models])}")
        user_input = inputs.get('user_input', None)
        rag_type = inputs['rag_type']
        if user_input is None:
            raise ValueError("Missing user input parameter!")
        context = ""
        relevant_documents = []
        if rag_type != "none":
            embeddings = OllamaEmbeddings(temperature=EMBEDDING_TEMPERATURE, model=EMBEDDING_MODEL)
            chroma_path = f"chroma/{EMBEDDING_MODEL}"
            if args.custom_vectorstore:
                chroma_path = args.custom_vectorstore
            vectorstore = Chroma(persist_directory=chroma_path,
                                 embedding_function=embeddings)
            relevant_documents = vectorstore.similarity_search_with_score(
                query=user_input, k=RAG_DOCUMENT_COUNT,
                filter={
                    "text_source": rag_type
                }
            )

            context += "\n\nThe following text is context provided by RAG model: \n" + '\n'.join(
                [document[0].page_content for document in relevant_documents])
            print(f"RAG used! Document count: {str(len(relevant_documents))}")
        user_message = {
            'role': 'user',
            'content': user_input + context,
        }
        if len(history) == 0:
            dos = (
                "Provide a conversational answer. "
                "Use RAG model provided context where it is appropriate."
            )
            donts = (
                    "Do not respond with anything that might cause XSS. "
                    + "If you don't know the answer, just say \"I do not know.\" Don't make up an answer. "
            )
            sys_message = {
                'role': 'system',
                'content': "You are a helpful assistant. "
                           + "You are given a user question and extracted parts of long documents by RAG model. "
                           + dos
                           + donts
            }
            messages = [sys_message, user_message]
        else:
            messages = []
            for message_item in history:
                messages.append(
                    {
                        "role": message_item.role,
                        "content": message_item.content,
                    }
                )
            messages.append(user_message)
        rag_sources = json.dumps(
            [{"id": x[0].id, "similarity_score": x[1], "metadata": x[0].metadata, "content": x[0].page_content} for x in
             relevant_documents])

        current_context_len = int(sum([len(x["content"]) for x in messages])/5)
        # TODO: thinking handling think=True
        response = ollama.chat(
            model=llm_model,
            messages=messages,
            options={
                # "num_predict": LLM_NUM_PREDICT,
                # "num_ctx": current_context_len,
                "seed": RANDOM_SEED,
            }
        )
        result = response['message']['content']
        # TODO: implement train of thought next version
        train_of_thought = ''
        if hasattr(response, "thinking"):
            train_of_thought = response['message']['thinking']
        messages.append({"role": "assistant", "content": result})
    except Exception as e:
        print(repr(e))
        raise ()

    return result, rag_sources, train_of_thought


@app.route('/', methods=['GET', 'POST'])
def lobby():
    user_id = get_or_set_user_id()
    resp = make_response(render_template('lobby.html'))
    resp.set_cookie(COOKIE_USER_ID, user_id)
    return resp


@app.route('/create_room', methods=['POST'])
def create_room():
    data = request.get_json()
    # Escape user input
    name = escape(data.get('name'))
    if not name:
        return jsonify({'error': 'Missing name'}), 400
    import uuid
    room_id = uuid.uuid4().hex
    existing = ChatRoom.query.filter_by(name=name, active=False).first()
    if existing:
        existing.name = name + "_" + str(datetime.datetime.now(datetime.UTC).timestamp())
        db.session.commit()
    new_room = ChatRoom(id=room_id, name=name)
    db.session.add(new_room)
    db.session.commit()
    emit_rooms_update()  # Immediately push update to everyone
    return jsonify({'id': room_id, 'name': name})

@socketio.on('remove_room')
def remove_room(data):
    room_id = data['room_id']
    room = ChatRoom.query.filter_by(id=room_id).first()
    if room:
        room.active = False
        db.session.commit()
        print(f"Room deactivated: {room_id}")
    emit_rooms_update()

@app.route('/rooms')
def list_rooms():
    rooms = ChatRoom.query.filter_by(active=True).all()
    return [r.as_dict() for r in rooms]


# Broadcast room info (name, id, user count)
def emit_rooms_update():
    rooms = ChatRoom.query.filter_by(active=True).all()
    payload = [r.as_dict() for r in rooms]
    print(payload)
    socketio.emit('rooms_list', payload)


@socketio.on('join_room')
def on_join(data):
    room_id = data['room_id']
    username = data.get('username', 'Anonymous')
    join_room(room_id)
    emit_rooms_update()


@app.route('/chat/<room_id>')
def chat(room_id):
    chat_room: Optional[ChatRoom] = ChatRoom.query.get(room_id)
    if chat_room is not None:
        sid = get_or_set_user_id()
        resp = make_response(render_template('chat.html.j2', room=chat_room.as_dict(), room_name=chat_room.name, llmlist=get_ollama_model_list()))
        resp.set_cookie(COOKIE_USER_ID, sid)
        return resp
    else:
        return "Chat room '%s' does not exist" % room_id, 404


@app.route('/room_history/<room_id>')
def room_history(room_id):
    messages = RoomMessage.query.filter_by(room_id=room_id).order_by(RoomMessage.timestamp).all()
    return [m.as_dict() for m in messages]


@app.route('/download_message/<int:msg_id>')
def download_message(msg_id):
    # Fetch the message ensuring user access
    msg = RoomMessage.query.filter_by(id=msg_id).first()
    if not msg:
        abort(404)
    # Download as text, safe headers
    return Response(
        msg.content,
        mimetype='text/plain',
        headers={"Content-Disposition": f"attachment;filename=raw_assistant_reply_{msg_id}.txt"}
    )


@app.route('/download_rag_sources/<int:msg_id>')
def download_rag_sources(msg_id):
    # Fetch the message ensuring user access
    msg = RoomMessage.query.filter_by(id=msg_id).first()
    if not msg:
        abort(404)
    # Download as text, safe headers
    return Response(
        msg.rag_sources,
        mimetype='text/plain',
        headers={"Content-Disposition": f"attachment;filename=rag_sources_{msg_id}.json"}
    )


@socketio.on('message')
def handle_message(data):
    # TODO: log model and rag_type used
    sid = request.cookies.get(COOKIE_USER_ID)
    room_id = data['room_id']
    username = data.get('username', 'Anonymous')
    user_text = data.get('user_input', '')

    # Save user message

    user_message = RoomMessage(room_id=room_id, username=username, role='user', content=user_text)
    db.session.add(user_message)
    db.session.commit()

    emit('message', user_message.as_dict(), to=room_id)
    log_llm_request(data, 'user')

    if args.production:
        history_query = RoomMessage.query.filter_by(room_id=room_id).all()
        assistant_text, rag_sources, train_of_thought = ollama_chat(data, room_id, username, history_query)
    else:
        time.sleep(args.test_delay_seconds if args.test_delay_seconds else 1)
        assistant_text = """
<h1>Lorem Ipsum</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. </p>
<h2>Lorem Ipsum</h2>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. </p>
<ul>
<li>Lorem Ipsum</li>
<li>Lorem Ipsum</li>
<li>Lorem Ipsum</li>
<li>Lorem Ipsum</li>
</ul>


        """
        source_example = {"document": "example_doc.pdf", "page": 42, "text": "Lorem ipsum, lorem ipsum, lorem ipsum."}
        rag_sources = json.dumps([source_example, source_example, source_example])
        train_of_thought = "I think therefore I think."

    log_llm_request(assistant_text, 'assistant')

    # Save assistant reply
    assistant_msg = RoomMessage(room_id=room_id, username=username, role='assistant', content=assistant_text,
                                rag_sources=rag_sources)
    db.session.add(assistant_msg)
    db.session.commit()
    emit('message', assistant_msg.as_dict(), to=room_id)
    print("Successful message!")


if __name__ == '__main__':
    logger_setup()
    with app.app_context():
        # Create db, if none
        db.create_all()
    # p = Thread(target=scheduler)
    # p.start()
    socketio.run(app, debug=(not args.production), use_reloader=False, allow_unsafe_werkzeug=True, host="0.0.0.0")
