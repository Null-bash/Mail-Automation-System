# test/auth/test_login.py
from unittest.mock import patch, MagicMock
from core.auth.login import login


def make_mock_conn(fetchone_return):
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


def test_login_success(monkeypatch, capsys):
    inputs = iter(["alice@example.com", "correct-password"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    fake_user = (1, "alice", "alice@example.com", "correct-password")
    mock_conn, mock_cur = make_mock_conn(fake_user)

    with patch("core.auth.login.get_connection", return_value=mock_conn):
        result = login()

    mock_cur.execute.assert_called_once()
    query, params = mock_cur.execute.call_args[0]
    assert params == ("alice@example.com", "correct-password")
    assert "SELECT" in query
    assert "users" in query

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

    captured = capsys.readouterr()
    assert "Welcome alice!" in captured.out
    assert result == fake_user


def test_login_invalid_credentials(monkeypatch, capsys):
    inputs = iter(["bob@example.com", "wrong-password"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(None)

    with patch("core.auth.login.get_connection", return_value=mock_conn):
        result = login()

    captured = capsys.readouterr()
    assert "Invalid Credentials!" in captured.out
    assert result is None

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_login_always_closes_connection_and_cursor(monkeypatch):
    inputs = iter(["someone@example.com", "whatever"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(None)

    with patch("core.auth.login.get_connection", return_value=mock_conn):
        login()

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()