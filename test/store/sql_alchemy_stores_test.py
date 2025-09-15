import os
import unittest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from store.sql_alchemy_stores import SQLAlchemy_ChatStore
from store_test import ChatStore_TestCase

db_file = 'test_data.db'
db_file_path = os.path.join('instance', db_file)


class SQLAlchemy_ChatStore_TestCase(ChatStore_TestCase):
    def setUp(self):
        super().setUp()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file
        self.app = app
        db = SQLAlchemy(app)
        self.db = db
        self.store = SQLAlchemy_ChatStore(db, app)

    def test_read_empty(self):
        with self.app.app_context():
            super().test_read_empty()

    def test_create_room(self):
        with self.app.app_context():
            super().test_create_room()

    def test_rename_room(self):
        with self.app.app_context():
            super().test_rename_room()

    def test_delete_room(self):
        with self.app.app_context():
            super().test_delete_room()

    def test_add_message(self):
        with self.app.app_context():
            super().test_add_message()


if __name__ == '__main__':
    unittest.main()
