"""Unit tests for the authentication login module.

This test suite uses pytest and unittest.mock to verify the behavior
of the login process, including successful authentication, handling
of invalid credentials, deactivated accounts, and proper database
connection management.
"""

from unittest.mock import MagicMock, patch

from core.auth.login import login


def make_mock_conn(fetchone_return, columns=None) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchone_return (tuple or None): The value to be returned by the
            mock cursor's `fetchone()` method, representing a simulated
            database record or lack thereof.
        columns (list[str] or None): Column names to expose via
            cur.description, mimicking the DB-API description format
            (a sequence of sequences where index 0 is the column name).
            Required whenever login() will reach the point of building
            `columns = [desc[0] for desc in cur.description]`, i.e.
            whenever fetchone_return is not None.

    Returns:
        tuple: A tuple containing the mock connection object and the mock
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    if columns is not None:
        mock_cur.description = [(col,) for col in columns]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


# Mirrors a `SELECT *` row shape from the `users` table.
COLUMNS = ["user_id", "name", "email", "password_hash", "role", "is_active"]


def test_login_success(monkeypatch, capsys) -> None:
    """Tests a successful user login scenario.

    Simulates standard input for a valid email and password. Mocks the
    database connection to return a valid, active user record and mocks
    bcrypt.checkpw to simulate a matching password. Asserts that the
    correct SQL query is executed, database connections are properly
    closed, the welcome message is printed, and the function returns
    the expected user data.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["alice@example.com", "correct-password"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    fake_user = (1, "alice", "alice@example.com", "hashed-value", "EMPLOYEE", True)
    mock_conn, mock_cur = make_mock_conn(fake_user, columns=COLUMNS)

    with patch("core.auth.login.get_connection", return_value=mock_conn), \
         patch("core.auth.login.bcrypt.checkpw", return_value=True) as mock_checkpw:
        result = login()

    mock_cur.execute.assert_called_once()
    query, params = mock_cur.execute.call_args[0]
    assert params == ("alice@example.com",)
    assert "SELECT" in query
    assert "users" in query

    mock_checkpw.assert_called_once_with(b"correct-password", b"hashed-value")

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

    captured = capsys.readouterr()
    assert "Welcome alice!" in captured.out
    assert result == fake_user


def test_login_wrong_password(monkeypatch, capsys) -> None:
    """Tests a failed login when the email exists but the password is wrong.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["alice@example.com", "wrong-password"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    fake_user = (1, "alice", "alice@example.com", "hashed-value", "EMPLOYEE", True)
    mock_conn, mock_cur = make_mock_conn(fake_user, columns=COLUMNS)

    with patch("core.auth.login.get_connection", return_value=mock_conn), \
         patch("core.auth.login.bcrypt.checkpw", return_value=False):
        result = login()

    captured = capsys.readouterr()
    assert "Invalid Credentials!" in captured.out
    assert result is None


def test_login_deactivated_account(monkeypatch, capsys) -> None:
    """Tests that a correct password on a deactivated account is rejected.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["alice@example.com", "correct-password"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    fake_user = (1, "alice", "alice@example.com", "hashed-value", "EMPLOYEE", False)
    mock_conn, mock_cur = make_mock_conn(fake_user, columns=COLUMNS)

    with patch("core.auth.login.get_connection", return_value=mock_conn), \
         patch("core.auth.login.bcrypt.checkpw", return_value=True):
        result = login()

    captured = capsys.readouterr()
    assert "deactivated" in captured.out
    assert result is None


def test_login_invalid_credentials(monkeypatch, capsys) -> None:
    """Tests a failed user login scenario when the email doesn't exist.

    Simulates standard input for an email and password. Mocks the
    database connection to return no matching record (None). Asserts
    that the invalid credentials message is printed, the function
    returns None, and database resources are properly closed.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
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


def test_login_always_closes_connection_and_cursor(monkeypatch) -> None:
    """Tests that database connections are always closed during login.

    Simulates a login attempt where the email isn't found and verifies
    that the `close()` methods on both the cursor and connection objects
    are called exactly once to prevent resource leaks.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    inputs = iter(["someone@example.com", "whatever"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(None)

    with patch("core.auth.login.get_connection", return_value=mock_conn):
        login()

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()