import argparse
import json
import uuid
from typing import List, Optional

from flask import request, render_template, session, make_response, abort, Response, jsonify
from flask_socketio import emit, join_room
from markupsafe import escape

from app_modules.llm_module import LLMModule
from app_modules.settings_module import SettingsModule
from app_modules.kb_module import KBModule
from config import app, db, settings, socketio
from config import RAG_DOCUMENT_COUNT
from domain import ChatRoom, RoomMessage
from knowledge_base import SuperKBStore, SuperDocSource, KBStore, DocSource
from knowledge_base_service import KnowledgeBaseService
from llm_runners.debug_runner import DebugRunner
from llm_runners.llm_runner import ChatContext, LLMRunner, SuperRunner
from logger import logger
from settings import DEFAULT_SYSTEM_PROMPT, LLM_RUNNERS, KBSTORES, DOC_SOURCES, RESTORE_DEFAULT
from store.sql_alchemy_stores import SQLAlchemy_ChatStore
from utils import utc_now

chat_store = SQLAlchemy_ChatStore(db, app)

def handle_settings_updated(name):
    if name in [RESTORE_DEFAULT, LLM_RUNNERS, KBSTORES, DOC_SOURCES]:
        update_module_deps()

@app.route('/', methods=['GET'])
def lobby():
    resp = make_response(render_template('lobby.html'))
    return resp

@app.route('/settings', methods=['GET'])
def settings_page():
    resp = make_response(render_template('settings.html'))
    return resp

@app.route('/knowledge-base', methods=['GET'])
def knowledge_base_page():
    resp = make_response(render_template('knowledge-base-page.html'))
    return resp

@app.route('/create_room', methods=['POST'])
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


@app.route('/rooms')
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
    # TODO: remove
    emit_rooms_update()


@app.route('/chat/<room_id>')
def chat(room_id):
    chat_room: Optional[ChatRoom] = chat_store.get_room_by_id(room_id)
    if chat_room is not None:
        kb_list = [None] + [x.name for x in kb_service.kb_store.list()]
        resp = make_response(render_template('chat.html.j2', room=chat_room.as_dict(), room_name=chat_room.name,
                                             llm_list=super_runner.list_chat_models(), kb_list=kb_list))
        return resp
    else:
        return "Chat room '%s' does not exist" % room_id, 404


@app.route('/room_history/<room_id>')
def room_history(room_id):
    messages = chat_store.messages_by_room(room_id)
    return [m.as_dict() for m in messages]


@app.route('/download_message/<int:msg_id>')
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


@app.route('/download_rag_sources/<int:msg_id>')
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


@socketio.on('message')
def handle_message(data):
    room_id = data['room_id']
    username = data.get('username', 'Anonymous')
    user_text = data.get('user_input', '')
    kb_name = data.get('kb_name', None)
    # Save user message
    raw_user_message = RoomMessage(room_id=room_id, username=username, role='user', content=user_text)

    emit('message', raw_user_message.as_dict(), to=room_id)
    log_llm_request(data, 'user')

    history_query = chat_store.messages_by_room(room_id)
    system_prompt = settings.get(DEFAULT_SYSTEM_PROMPT, '')

    user_input = data.get('user_input', None)
    if user_input is None:
        raise ValueError("Missing user input parameter!")
    assistant_text, rag_sources = super_runner.chat(
        ChatContext(
            data.get('llm_model'),
            system_prompt,
            RAG_DOCUMENT_COUNT,
            kb_service.kb_store.get(kb_name)
        ),
        room_id,
        user_input,
        update_callback=lambda msg: emit('progress', msg.as_dict(), to=room_id),
        history=history_query
    )

    log_llm_request(assistant_text, 'assistant')

    # Adding only if generating message was a success. Otherwise it would show previous user message that did not contribute to chat.
    # Adding rag_sources to both user and assistant. User message requires it for correct chat history,
    # assitant needs it to have a reference in its chat message in frontend
    user_message = RoomMessage(room_id=room_id, username=username, role='user', content=user_text,
                               rag_sources=rag_sources)
    assistant_msg = RoomMessage(room_id=room_id, username=data.get('llm_model'), role='assistant', content=assistant_text,
                                rag_sources=rag_sources)
    chat_store.add_message(user_message)
    message_id = chat_store.add_message(assistant_msg)
    assistant_msg.id = message_id

    emit('message', assistant_msg.as_dict(), to=room_id)


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

    if not args.production:
        runner_list.append(DebugRunner())
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
        current_runners = settings.get_llm_runners()
        for runner in list(current_runners):
            if runner["type"] == "debug":
                current_runners.remove(runner)
        settings["llm_runners"] = current_runners
    else:
        print("Running in debug mode. For production mode add --production to parameters.")
        current_runners = settings.get_llm_runners()
        for runner in list(current_runners):
            if runner["type"] == "debug":
                current_runners.remove(runner)
        current_runners.append({"type": "debug", "name": "debug"})
        settings["llm_runners"] = current_runners
    kb_module: Optional[KBModule] = None
    llm_module: Optional[LLMModule] = None
    update_module_deps()
    kb_module.apply_routes(app)
    llm_module.apply_routes(app)
    logger.info(f"App starting at {utc_now().isoformat()}")
    host = "127.0.0.1" if args.localhost else "0.0.0.0"
    socketio.run(app, debug=(not args.production), use_reloader=False, allow_unsafe_werkzeug=True, host=host)
