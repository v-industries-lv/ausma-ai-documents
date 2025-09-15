from abc import ABC, abstractmethod
from typing import List, Optional

from domain import ChatRoom, RoomMessage


class ChatStore(ABC):
    # Chat rooms
    @abstractmethod
    def list_active_rooms(self) -> List[ChatRoom]:
        pass

    @abstractmethod
    def list_deleted_rooms(self) -> List[ChatRoom]:
        pass

    @abstractmethod
    def get_room_by_id(self, room_id: str) -> Optional[ChatRoom]:
        pass

    @abstractmethod
    def create_room(self, room_id: str, name: str):
        pass

    @abstractmethod
    def rename_room(self, room_id: str, room_name: str) -> bool:
        pass

    @abstractmethod
    def delete_room(self, room_id: str) -> bool:
        pass

    @abstractmethod
    def restore_room(self, room_id: str) -> bool:
        pass

    @abstractmethod
    def permanently_delete_room(self, room_id: str) -> bool:
        pass

    # Chat messages
    @abstractmethod
    def messages_by_room(self, room_id: str) -> List[RoomMessage]:
        pass

    @abstractmethod
    def message_by_id(self, msg_id: str) -> Optional[RoomMessage]:
        pass

    @abstractmethod
    def add_message(self, msg: RoomMessage) -> int:
        pass
