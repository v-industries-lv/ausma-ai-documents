from typing import Dict
from threading import Lock


class RoomState:
    def __init__(self, room_id):
        self.room_id: str = room_id
        self.failed: bool = False

    def start(self):
        self.failed = False

    def stop(self):
        self.failed = True

    def is_stopped(self):
        return self.failed


class RoomStateRegister:
    def __init__(self):
        self.room_states: Dict[str, RoomState] = {}
        self.lock: Lock = Lock()

    def get(self, room_id: str) -> RoomState:
        if room_id not in self.room_states.keys():
            with self.lock:
                if room_id not in self.room_states.keys():
                    self.room_states[room_id] = RoomState(room_id)
        return self.room_states[room_id]