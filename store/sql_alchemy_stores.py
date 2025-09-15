from typing import List, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import domain
from store.store import ChatStore
from utils import utc_now


class SQLAlchemy_ChatStore(ChatStore):
    def __init__(self, db: SQLAlchemy, app: Flask):
        self.db = db
        self.app = app

        class ChatRoom(db.Model, domain.ChatRoom):
            id = db.Column(db.String(64), primary_key=True)
            name = db.Column(db.String(128), unique=False)
            created_at = db.Column(db.DateTime, default=utc_now)
            active = db.Column(db.Boolean, unique=False, default=True)
            settings_str = db.Column(db.Text)

            @staticmethod
            def from_domain(data: domain.ChatRoom):
                upcast = ChatRoom()
                upcast.id = data.id
                upcast.name = data.name
                upcast.created_at = data.created_at
                upcast.active = data.active
                upcast.settings_str = data.settings_str
                return upcast

        self.ChatRoom = ChatRoom

        class RoomMessage(db.Model, domain.RoomMessage):
            id = db.Column(db.Integer, primary_key=True)
            room_id = db.Column(db.String(64), db.ForeignKey('chat_room.id'))
            username = db.Column(db.String(64))  # or anonymous
            role = db.Column(db.String(16))  # 'user'/'assistant'
            content = db.Column(db.Text)
            rag_sources = db.Column(db.Text)
            timestamp = db.Column(db.DateTime, default=utc_now)

            @staticmethod
            def from_domain(data: domain.RoomMessage):
                upcast = RoomMessage()
                upcast.id = data.id
                upcast.room_id = data.room_id
                upcast.username = data.username
                upcast.role = data.role
                upcast.content = data.content
                upcast.rag_sources = data.rag_sources
                upcast.timestamp = data.timestamp
                return upcast

        self.RoomMessage = RoomMessage
        with app.app_context():
            db.create_all()

    # Chat rooms
    def list_active_rooms(self):
        return self.ChatRoom.query.filter_by(active=True).all()

    def list_deleted_rooms(self):
        return self.ChatRoom.query.filter_by(active=False).all()

    def get_room_by_id(self, room_id):
        return self.ChatRoom.query.get(room_id)

    def create_room(self, room_id: str, name: str):
        new_room = self.ChatRoom(id=room_id, name=name)
        self.db.session.add(new_room)
        self.db.session.commit()

    def rename_room(self, room_id: str, name: str) -> bool:
        room = self.ChatRoom.query.filter_by(id=room_id).first()
        if room is not None:
            room.name = name
            self.db.session.commit()
            return True
        else:
            return False

    def delete_room(self, room_id: str) -> bool:
        room = self.ChatRoom.query.filter_by(id=room_id).first()
        if room is not None:
            room.active = False
            self.db.session.commit()
            return True
        else:
            return False

    def restore_room(self, room_id: str) -> bool:
        room = self.ChatRoom.query.filter_by(id=room_id).first()
        if room is not None:
            room.active = True
            self.db.session.commit()
            return True
        else:
            return False

    def permanently_delete_room(self, room_id: str) -> bool:
        did_delete = self.ChatRoom.query.filter_by(id=room_id).delete() > 0
        self.RoomMessage.query.filter_by(room_id=room_id).delete()
        self.db.session.commit()
        return did_delete

    # Chat messages
    def messages_by_room(self, room_id: str) -> List[domain.RoomMessage]:
        return self.RoomMessage.query.filter_by(room_id=room_id).order_by(self.RoomMessage.timestamp).all()

    def message_by_id(self, msg_id: str) -> Optional[domain.RoomMessage]:
        return self.RoomMessage.query.filter_by(id=msg_id).first()

    def add_message(self, msg: domain.RoomMessage) -> int:
        user_message = self.RoomMessage.from_domain(msg)
        self.db.session.add(user_message)
        self.db.session.commit()
        return user_message.id
