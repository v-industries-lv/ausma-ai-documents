import datetime
import unittest
from abc import ABC

from domain import RoomMessage
from store.store import ChatStore


class ChatStore_TestCase(ABC, unittest.TestCase):
    """
    Generic test for all `ChatStore`s
    """

    def setUp(self):
        super().setUp()
        # placeholder so type hints are useful, need to override in implementations
        # noinspection PyTypeChecker
        self.store: ChatStore = None

    def test_read_empty(self):
        self.assertEqual([], self.store.list_active_rooms())
        self.assertEqual([], self.store.list_deleted_rooms())
        self.assertEqual(None, self.store.get_room_by_id('TEST_ROOM1'))
        self.assertEqual([], self.store.messages_by_room('TEST_ROOM1'))

    def test_create_room(self):
        room_id = 'TEST_ROOM1'
        name = 'room_name'
        self.store.create_room(room_id, name)

        room = self.store.get_room_by_id(room_id)
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        rooms = self.store.list_active_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        self.assertEqual([], self.store.list_deleted_rooms())


    def test_rename_room(self):
        room_id = 'TEST_ROOM1'
        name = 'room_name'
        self.store.create_room(room_id, name)

        room = self.store.get_room_by_id(room_id)
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        rooms = self.store.list_active_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        self.assertEqual([], self.store.list_deleted_rooms())

        new_cool_name = 'new_cool_name'
        self.assertTrue(self.store.rename_room(room_id, new_cool_name))

        room = self.store.get_room_by_id(room_id)
        self.assertEqual(room_id, room.id)
        self.assertEqual(new_cool_name, room.name)
        rooms = self.store.list_active_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(new_cool_name, room.name)
        self.assertEqual([], self.store.list_deleted_rooms())

    def test_delete_room(self):
        room_id = 'TEST_ROOM1'
        name = 'room_name'
        self.store.create_room(room_id, name)
        self.store.add_message(RoomMessage(id=1, room_id=room_id))
        self.store.add_message(RoomMessage(id=2, room_id=room_id))

        rooms = self.store.list_active_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        self.assertEqual([], self.store.list_deleted_rooms())
        self.assertEqual(2, len(self.store.messages_by_room(room_id)))

        self.store.delete_room(room_id)

        self.assertEqual([], self.store.list_active_rooms())
        rooms = self.store.list_deleted_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        self.assertEqual(2, len(self.store.messages_by_room(room_id)))

        self.store.restore_room(room_id)

        rooms = self.store.list_active_rooms()
        self.assertEqual(1, len(rooms))
        room = rooms[0]
        self.assertEqual(room_id, room.id)
        self.assertEqual(name, room.name)
        self.assertEqual([], self.store.list_deleted_rooms())
        self.assertEqual(2, len(self.store.messages_by_room(room_id)))

        self.store.permanently_delete_room(room_id)
        self.assertEqual([], self.store.list_active_rooms())
        self.assertEqual([], self.store.list_deleted_rooms())
        self.assertEqual(0, len(self.store.messages_by_room(room_id)))

    def test_add_message(self):
        room_id = 'TEST_ROOM1'
        name = 'room_name'
        self.store.create_room(room_id, name)
        self.assertEqual([], self.store.messages_by_room(room_id))

        msg1 = RoomMessage(id=1, room_id=room_id, content='hey', timestamp=datetime.datetime(2020, 1, 20, 20, 1, 20))
        self.store.add_message(msg1)
        msgs = self.store.messages_by_room(room_id)
        self.assertEqual([msg1], msgs)

        msg2 = RoomMessage(id=2, room_id=room_id, content='hey', timestamp=datetime.datetime(2020, 1, 20, 20, 1, 21))
        self.store.add_message(msg2)
        msgs = self.store.messages_by_room(room_id)
        self.assertEqual([msg1, msg2], msgs)
