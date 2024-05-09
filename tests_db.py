import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from datetime import datetime
import db

class DBTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        db.db_setup(self.conn)  # Setup a memory database for testing
        # Insert data for testing
        self.conn.execute("INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);",
                          ('Original Title', '1,12', datetime.now(), datetime.now()))
        self.conn.commit()

    def test_db_get_connection(self):
        with patch('db.sqlite3.connect') as mocked_connect:
            db.db_get_connection()
            mocked_connect.assert_called_with('chats.db', check_same_thread=False)

    def test_db_get_threads(self):
        cursor = self.conn.cursor()
        expected_output = [(3, 'Example 2', '4,5,6'),
                           (2, 'Original Title', '1,12'),
                           (1, 'Example', '1,2,3')]
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

    @patch('db.datetime')  # Patching datetime class in helpers module.
    def test_db_update_title(self, mock_datetime):
        # Test updating the thread title and last use
        # Set up the mock to return a specific datetime when datetime.now() is called.
        mock_now = datetime(2022, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        new_title = "Updated Title"
        db.db_update_title(new_title, mock_now, 1, self.conn)
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, last_use FROM threads WHERE thread_id = 1;")
        result = cursor.fetchone()
        self.assertEqual(result[0], new_title)
        self.assertEqual(result[1], str(mock_now))

    def test_db_delete_thread(self):
        # Preparing additional data
        self.conn.execute("INSERT INTO messages (message_id, role, content, created) VALUES (12, 'user', 'Message 12', ?);", (datetime.now(),))
        self.conn.commit()

        # Deleting thread
        db.db_delete_thread(2, self.conn)

        # Verify messages deletion
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE message_id IN (1);")
        message_count = cursor.fetchone()[0]
        self.assertEqual(message_count, 1)  # Asserting that the messages was not deleted
        cursor.execute("SELECT COUNT(*) FROM messages WHERE message_id IN (12);")
        message_count = cursor.fetchone()[0]
        self.assertEqual(message_count, 0)  # Asserting that the messages was deleted

        # Verify thread deletion
        cursor.execute("SELECT COUNT(*) FROM threads WHERE thread_id = 2;")
        thread_count = cursor.fetchone()[0]
        self.assertEqual(thread_count, 0)  # Asserting that the thread was deleted

    def tearDown(self):
        self.conn.close()


if __name__ == '__main__':
    unittest.main()