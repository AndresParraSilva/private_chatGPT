import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from datetime import datetime
import db

class DBTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        db.db_setup(self.conn)  # Setup a memory database for testing

    def test_db_get_connection(self):
        with patch('db.sqlite3.connect') as mocked_connect:
            db.db_get_connection()
            mocked_connect.assert_called_with('chats.db', check_same_thread=False)

    def test_db_get_threads(self):
        cursor = self.conn.cursor()
        expected_output = [(2, 'Example 2', '4,5,6'), (1, 'Example', '1,2,3')]
        cursor.execute("INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);",
                       ('Example 2', '4,5,6', datetime.now(), datetime.now()))
        self.conn.commit()
        result = db.db_get_threads(self.conn)
        self.assertEqual(result, expected_output)

    def test_db_insert_message(self):
        count_before = self.conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        db.db_insert_message('user', 'New Message', datetime.now(), self.conn)
        count_after = self.conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        self.assertEqual(count_after, count_before + 1)

    def test_db_insert_thread(self):
        count_before = self.conn.execute('SELECT COUNT(*) FROM threads').fetchone()[0]
        db.db_insert_thread('New Thread', '1', datetime.now(), datetime.now(), self.conn)
        count_after = self.conn.execute('SELECT COUNT(*) FROM threads').fetchone()[0]
        self.assertEqual(count_after, count_before + 1)

    def tearDown(self):
        self.conn.close()

if __name__ == '__main__':
    unittest.main()