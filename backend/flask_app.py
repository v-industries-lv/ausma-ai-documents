import argparse
import json
import os.path
import uuid
from typing import List, Optional, Dict

from flask import request, session, abort, Response, jsonify, send_from_directory, send_file
from flask_socketio import emit, join_room, leave_room
from markupsafe import escape

from app_modules.llm_module import LLMModule
from app_modules.settings_module import SettingsModule
from app_modules.kb_module import KBModule
from config import app, db, settings, socketio
from domain import ChatRoom, RoomMessage, MessageProgress
from kb.knowledge_base import SuperKBStore, KBStore
from doc_sources.doc_source import DocSource, SuperDocSource
from knowledge_base_service import KnowledgeBaseService
from generation_guard import GenerationGuard
from llm_runners.debug_runner import DebugRunner
from llm_runners.llm_runner import ChatContext, LLMRunner, SuperRunner
from logger import logger
from settings import DEFAULT_SYSTEM_PROMPT, LLM_RUNNERS, KBSTORES, DOC_SOURCES, RESTORE_DEFAULT, GENERATION_GUARD, RAGSettings
from store.sql_alchemy_stores import SQLAlchemy_ChatStore
from utils import utc_now
from room_states import RoomStateRegister, RoomState

chat_store = SQLAlchemy_ChatStore(db, app)

def handle_settings_updated(name):
    if name in [RESTORE_DEFAULT, LLM_RUNNERS, KBSTORES, DOC_SOURCES]:
        update_module_deps()


def host_frontend(base_path):
    logger.info("Hosting frontend from " + base_path)
    @app.route('/', methods=['GET'])
    def root():
        return front_end()

    @app.route('/assets/<path:path>')
    def assets(path):
        return send_from_directory(base_path + '/assets', path)

    @app.route('/about/', methods=['GET'])
    @app.route('/about', methods=['GET'])
    def about():
        return front_end()

    @app.route('/settings/', methods=['GET'])
    @app.route('/settings', methods=['GET'])
    def settings_():
        return front_end()

    @app.route('/knowledge-base/', methods=['GET'])
    @app.route('/knowledge-base', methods=['GET'])
    def knowledge_base():
        return front_end()

    @app.route('/chat/<path:path>')
    def chat(path):
        return front_end()


    def front_end():
        return send_file(base_path + '/index.html')

    @app.route('/static/<path:path>')
    def static(path):
        return send_from_directory(base_path + '/static', path)


frontend_path = None
if os.path.isdir("frontend"):
    # bundled
    # working directory is the root of the bundle, but paths are relative to the flask_app.py
    frontend_path = "../../frontend"
elif os.path.isdir("../frontend/dist"):
    # running in development
    frontend_path = '../frontend/dist'
if frontend_path is not None:
    host_frontend(frontend_path)
else:
    logger.warning("No frontend code present, only running /api")


@app.route('/api/create_room/', methods=['POST'])
@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.get_json()
    # Escape user input
    name = escape(data.get('name'))
    if not name:
        return jsonify({'error': 'Missing name'}), 400

    room_id = uuid.uuid4().hex
    chat_store.create_room(room_id, name)
    logger.info(f"[ROOMS]Room created: {room_id}")
    emit_rooms_update()  # Immediately push update to everyone
    return jsonify({'id': room_id, 'name': name})


@socketio.on('remove_room')
def remove_room(data):
    room_id = data['room_id']
    if chat_store.delete_room(room_id):
        logger.info(f"[ROOMS]Room deactivated: {room_id}")
    emit_rooms_update()

@app.route('/api/room/<room_id>/rename/<name>')
def rename_room(room_id, name):
    if chat_store.rename_room(room_id, name):
        emit_rooms_update()
        return "Success"
    return "Failed!"

@app.route('/api/rooms/')
@app.route('/api/rooms')
def list_rooms():
    rooms = chat_store.list_active_rooms()
    return [r.as_dict() for r in rooms]


# Broadcast room info (name, id, user count)
def emit_rooms_update():
    rooms = chat_store.list_active_rooms()
    payload = [r.as_dict() for r in rooms]
    socketio.emit('rooms_list', payload)


@socketio.on('join_room')
def on_join(data):
    room_id = data['room_id']
    join_room(room_id)


@socketio.on('leave_room')
def on_leave(data):
    room_id = data['room_id']
    leave_room(room_id)


@app.route('/api/room/<room_id>')
def room_info(room_id):
    chat_room: Optional[ChatRoom] = chat_store.get_room_by_id(room_id)
    if chat_room is not None and chat_room.active:
        return chat_room.as_dict()
    else:
        return {}, 404


@app.route('/api/room_history/<room_id>')
def room_history(room_id):
    messages = chat_store.messages_by_room(room_id)
    return [m.as_dict() for m in messages]


@app.route('/api/message/<int:msg_id>')
def download_message(msg_id):
    # Fetch the message ensuring user access
    msg = chat_store.message_by_id(msg_id)
    if not msg:
        abort(404)
    # Download as text, safe headers
    return Response(
        msg.content,
        mimetype='text/plain',
        headers={"Content-Disposition": f"attachment;filename=raw_assistant_reply_{msg_id}.txt"}
    )


@app.route('/api/message/<int:msg_id>/rag')
def download_rag_sources(msg_id):
    # Fetch the message ensuring user access
    msg = chat_store.message_by_id(msg_id)
    if not msg:
        abort(404)
    # Download as text, safe headers
    rag_sources = None if msg.rag_sources is None else json.loads(msg.rag_sources)
    return Response(
        json.dumps(rag_sources, indent=2),
        mimetype='text/plain',
        headers={"Content-Disposition": f"attachment;filename=rag_sources_{msg_id}.json"}
    )

# TODO: Combine these
last_progress: Dict[str, MessageProgress] = {}
room_state_register: RoomStateRegister = RoomStateRegister()

def emit_progress(msg, room_id):
    last_progress[room_id] = msg
    emit('progress', (msg.as_dict(), room_id), to=room_id),


@app.route('/api/room/<room_id>/progress')
def get_last_progress(room_id):
    last = last_progress.get(room_id)
    if last is not None:
        return last.as_dict()
    else:
        return "null"

@app.route('/api/room/<room_id>/stop')
def stop_chat_generation(room_id):
    room_state_register.get(room_id).stop()
    return f"Stopping LLM in room {room_id}..."

@socketio.on('message')
def handle_message(data):
    room_id = data['room_id']
    room_state: RoomState = room_state_register.get(room_id)
    room_state.start()
    try:
        username = data.get('username', 'Anonymous')
        user_text = data.get('user_input', '')
        kb_name = data.get('kb_name', None)
        model = data.get('llm_model')
        # send temporary use message (id=null)
        raw_user_message = RoomMessage(room_id=room_id, username=username, role='user', content=user_text)

        emit_progress(MessageProgress('started', 0, 0, 0), room_id)
        emit('message', (raw_user_message.as_dict(), room_id), to=room_id)
        log_llm_request(data, 'user')

        history_query = chat_store.messages_by_room(room_id)
        cleaned_history = [x for x in history_query if not x.failed]
        system_prompt = settings.get(DEFAULT_SYSTEM_PROMPT, '')

        user_input = data.get('user_input', None)
        gen_guard = GenerationGuard.from_settings(settings[GENERATION_GUARD])
        if user_input is None:
            raise ValueError("Missing user input parameter!")
        if not super_runner.is_model_installed(model=model):
            raise ValueError(f"Did not find model: {model}! Check if model is installed and the LLM runner is enabled!")
        try:
            system_text, assistant_text, rag_sources = super_runner.chat(
                ChatContext(
                    model,
                    system_prompt,
                    kb_service.kb_store.get(kb_name)
                ),
                room_state,
                user_input,
                gen_guard=gen_guard,
                update_callback=lambda msg: emit_progress(msg, room_id),
                history=cleaned_history,
                rag_settings=RAGSettings.from_settings(settings),
            )
        except Exception as e:
            emit_progress(MessageProgress('error', 0, 0, 0, message=f"{e}"), room_id)
            logger.error(f"LLM runner chat failed. Error: {e}")
            room_state.stop()
            return
        log_llm_request(assistant_text, 'assistant')

        # Adding only if generating message was a success. Otherwise, it would show previous user message that did not contribute to chat.
        # Adding rag_sources to both user and assistant. User message requires it for correct chat history,
        # assitant needs it to have a reference in its chat message in frontend
        has_system_prompt_history = any([x.role == "system" for x in cleaned_history])
        if not has_system_prompt_history:
            system_message = RoomMessage(room_id=room_id, username="__system__", role="system",
                                         content=system_text,
                                         rag_sources=None,
                                         failed=room_state.failed
                                         )
            chat_store.add_message(system_message)
        user_message = RoomMessage(room_id=room_id, username=username, role='user',
                                   content=user_text,
                                   rag_sources=rag_sources,
                                   failed=room_state.failed
                                   )
        assistant_msg = RoomMessage(room_id=room_id, username=data.get('llm_model'), role='assistant',
                                    content=assistant_text,
                                    rag_sources=rag_sources,
                                    failed=room_state.failed
                                    )
        user_message_id = chat_store.add_message(user_message)
        user_message.id = user_message_id
        message_id = chat_store.add_message(assistant_msg)
        assistant_msg.id = message_id

        emit('message', (user_message.as_dict(), room_id), to=room_id)
        emit('message', (assistant_msg.as_dict(), room_id), to=room_id)
        if not room_state.failed:
            emit_progress(MessageProgress('finished', 0, 0, 0), room_id)
    except Exception as e:
        logger.error(f"Error occurred while handling message. Error: {e}")
        emit_progress(MessageProgress('error', 0, 0, 0, message=f"{e}"), room_id)
    finally:
        room_state.stop()

def log_llm_request(log_data, role):
    user_id = session.get('user_id')
    timestamp = utc_now().isoformat() + "Z"
    try:
        payload = json.dumps(log_data)
    except Exception as e:
        payload = '"BAD_LOG_PAYLOAD"'

    entry = f"[LLM_REQUEST]_{user_id}_{timestamp}_{role}_{payload}"
    logger.info(entry)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--production', action='store_true', help='Use production config.')
    parser.add_argument('--localhost', action='store_true', help='Only listen for local connections')
    args = parser.parse_args()
    return args


def update_module_deps():
    # TODO: stop (and then restart?) the kb_service on config change.
    global super_runner
    global kb_service
    global kb_module
    global llm_module

    runner_list: List[LLMRunner] = LLMRunner.from_settings(settings)
    kb_stores: List[KBStore] = KBStore.from_settings(settings)

    super_runner = SuperRunner(runner_list)
    kb_store = SuperKBStore(kb_stores)
    doc_sources = DocSource.from_settings(settings)
    doc_source = SuperDocSource(doc_sources=doc_sources)
    kb_service = KnowledgeBaseService(
        kb_store,
        doc_source,
        super_runner
    )
    if kb_module is not None:
        kb_module.kb_service = kb_service
    else:
        kb_module = KBModule(kb_service)

    if llm_module is not None:
        llm_module.llm_runners = super_runner
    else:
        llm_module = LLMModule(super_runner)


if __name__ == '__main__':
    args = parse_args()
    SettingsModule(settings).apply_routes(app, handle_settings_updated)
    if args.production:
        print("Running in production mode.")
    else:
        print("Running in debug mode. For production mode add --production to parameters.")
    kb_module: Optional[KBModule] = None
    llm_module: Optional[LLMModule] = None
    update_module_deps()
    kb_module.apply_routes(app)
    llm_module.apply_routes(app)
    logger.info(f"App starting at {utc_now().isoformat()}")
    host = "127.0.0.1" if args.localhost else "0.0.0.0"
    socketio.run(app, debug=(not args.production), use_reloader=False, allow_unsafe_werkzeug=True, host=host)
