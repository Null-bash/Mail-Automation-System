"""Unit tests for database connection handling.

This test suite uses pytest and unittest.mock to verify that `get_connection`
correctly initializes and returns a database connection using the expected
configuration parameters.
"""

from unittest.mock import MagicMock, patch

from core.db import get_connection


def test_get_connection_calls_psycopg_with_correct_args() -> None:
    """Tests that `get_connection` calls `psycopg.connect` with the correct arguments."""
    with patch("core.db.psycopg.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        conn = get_connection()

        mock_connect.assert_called_once_with(
            host="localhost",
            port=5431,
            dbname="Mail Automation System",
            user="postgres",
            password="20031382Ss@",
        )
        assert conn is mock_connect.return_value