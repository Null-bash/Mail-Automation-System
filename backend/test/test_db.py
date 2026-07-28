# test/test_db.py
from unittest.mock import patch, MagicMock
from core.db import get_connection


def test_get_connection_calls_psycopg_with_correct_args():
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