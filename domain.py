import datetime
from typing import Optional
import markdown
import nh3

import utils


class ChatRoom:
    def __init__(self, id=None, name=None, created_at=None, active=None, settings_str=None):
        self.id: Optional[str] = id
        self.name: Optional[str] = name
        self.created_at: Optional[datetime.datetime] = created_at
        self.active: Optional[bool] = active
        self.settings_str: Optional[str] = settings_str

    def __eq__(self, other):
        if isinstance(other, ChatRoom):
            return (
                    self.id == other.id
                    and self.name == other.name
                    and self.created_at == other.created_at
                    and self.active == other.active
                    and self.settings_str == other.settings_str
            )
        return False

    def __repr__(self):
        return f'ChatRoom({self.id},name={repr(self.name)},created_at={repr(self.created_at)},active={self.active},settings_str={repr(self.settings_str)})'

    def as_dict(self):
        return {"id": self.id, "name": self.name, "created": self.created_at.strftime("%Y-%m-%d_%H:%M:%S")}


class RoomMessage:
    def __init__(self, id=None, room_id=None, username=None, role=None, content=None, rag_sources=None, timestamp=None):
        self.id: Optional[int] = id
        self.room_id: Optional[str] = room_id
        self.username: Optional[str] = username
        self.role: Optional[str] = role
        self.content: Optional[str] = content
        self.rag_sources: Optional[str] = rag_sources
        self.timestamp: Optional[datetime.datetime] = timestamp if timestamp is not None else utils.utc_now()

    def __eq__(self, other):
        if isinstance(other, RoomMessage):
            return (
                    self.id == other.id
                    and self.room_id == other.room_id
                    and self.username == other.username
                    and self.role == other.role
                    and self.content == other.content
                    and self.rag_sources == other.rag_sources
                    and self.timestamp == other.timestamp
            )
        return False

    def __repr__(self):
        return f'RoomMessage({self.id},room_id={repr(self.room_id)},username={repr(self.username)},role={repr(self.role)},content={repr(self.content)},rag_sources={repr(self.rag_sources)},timestamp={repr(self.timestamp)})'

    def as_dict(self):
        extensions = [
            'fenced_code',
            'codehilite',
            'tables',
            'attr_list',
            'nl2br',
            'sane_lists',
        ]
        return {
            "id": self.id,
            "room_id": self.room_id,
            "username": self.username,
            "role": self.role,
            "content": markdown.markdown(nh3.clean(self.content), extensions=extensions),
            "rag_sources": self.rag_sources,
            "timestamp": self.timestamp.isoformat(),
        }


class MessageProgress:
    def __init__(self, new_tokens, duration_s, total_response_tokens):
        self.new_tokens = new_tokens
        self.duration_s = duration_s
        self.total_response_tokens = total_response_tokens

    def __eq__(self, other):
        if isinstance(other, MessageProgress):
            return (
                    self.new_tokens == other.new_tokens
                    and self.duration_s == other.duration_s
                    and self.total_response_tokens == other.total_response_tokens
            )
        return False

    def as_dict(self):
        return {
            "new_tokens": self.new_tokens,
            "duration_s": self.duration_s,
            "total_response_tokens": self.total_response_tokens,
        }
