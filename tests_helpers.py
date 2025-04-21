import unittest
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

import helpers


class TestHelpers(unittest.TestCase):
    def setUp(self):
        # Setup an in-memory database that can be used for testing.
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER PRIMARY KEY,
                title TEXT,
                messages TEXT,
                created TIMESTAMP,
                last_use TIMESTAMP
            )''')
        self.conn.commit()
        # Setup some thread titles for testing.
        self.conn.execute('INSERT INTO threads (title) VALUES (?)', ('Example (1)',))
        self.conn.execute('INSERT INTO threads (title) VALUES (?)', ('Example (2)',))
        self.conn.execute('INSERT INTO threads (title) VALUES (?)', ('Experiment (1)',))
        self.conn.commit()

    def test_get_new_thread_title_no_existing(self):
        """Test that a new unique title is given when no previous titles exist."""
        title = "New Thread"
        result = helpers.get_new_thread_title(title, self.conn)
        self.assertEqual(result, title)

    def test_get_new_thread_title_with_extension(self):
        """Test that a title is correctly incremented if similar titles exist."""
        title = "Example"
        result = helpers.get_new_thread_title(title, self.conn)
        self.assertEqual(result, "Example (3)")

    def test_get_new_thread_title_with_initial_number(self):
        """Test that a functional title increments correctly when it already includes a number."""
        title = "Experiment (1)"
        result = helpers.get_new_thread_title(title, self.conn)
        self.assertEqual(result, "Experiment (2)")

    @patch('helpers.get_new_thread_title')
    @patch('helpers.db_update_title')
    def test_change_title_same_title(self, mock_update_title, mock_get_new_thread_title):
        """Test no action is performed if the old title and new title are the same."""
        helpers.change_title(1, "A title", "A title", self.conn)
        mock_get_new_thread_title.assert_not_called()
        mock_update_title.assert_not_called()

    @patch('helpers.datetime')  # Patching datetime class in helpers module.
    def test_change_title_different_titles(self, mock_datetime):
        """Test the change_title logic when the titles actually differ."""
        # Set up the mock to return a specific datetime when datetime.now() is called.
        mock_now = datetime(2022, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        # Mock the other functions as before
        with patch('helpers.get_new_thread_title') as mock_get_new_thread_title, \
            patch('helpers.db_update_title') as mock_update_title:
            mock_get_new_thread_title.return_value = 'A title (2)'
            helpers.change_title(1, "A title", "A title (1)", self.conn)

            # Ensure the mocks were called correctly with the controlled datetime
            mock_get_new_thread_title.assert_called_once_with('A title (1)', self.conn)
            mock_update_title.assert_called_once_with('A title (2)', mock_now, 1, self.conn)

    def tearDown(self):
        self.conn.close()


if __name__ == '__main__':
    unittest.main()