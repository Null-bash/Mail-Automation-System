"""Unit tests for email update operations (reply functionality).

This test suite uses pytest and unittest.mock to verify the behavior of the
`reply_to_mail` function. It tests input validation (empty and whitespace-only
replies), handling of missing emails, successful reply submission, and
input text sanitization (whitespace stripping).
"""

from unittest.mock import MagicMock, patch

from core.crud.update import reply_to_mail


def make_mock_conn(fetchone_return) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchone_return (tuple | None): The value to be returned by the
            mock cursor's `fetchone()` method.

    Returns:
        tuple: A tuple containing the mock connection object and the mock 
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


def test_reply_to_mail_empty_body(monkeypatch, capsys) -> None:
    """Tests that replying fails and aborts if the reply body is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    with patch("core.crud.update.get_connection") as mock_get_conn:
        reply_to_mail(mail_id=1, current_user_id=2)

    mock_get_conn.assert_not_called()
    assert "Reply cannot be empty!" in capsys.readouterr().out


def test_reply_to_mail_body_whitespace_only(monkeypatch, capsys) -> None:
    """Tests that replying fails if the reply body consists only of whitespace.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    monkeypatch.setattr("builtins.input", lambda prompt="": "   ")

    with patch("core.crud.update.get_connection") as mock_get_conn:
        reply_to_mail(mail_id=1, current_user_id=2)

    mock_get_conn.assert_not_called()
    assert "Reply cannot be empty!" in capsys.readouterr().out


def test_reply_to_mail_mail_not_found(monkeypatch, capsys) -> None:
    """Tests that replying fails if the target mail ID does not exist.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    monkeypatch.setattr("builtins.input", lambda prompt="": "Thanks!")

    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.crud.update.get_connection", return_value=mock_conn):
        reply_to_mail(mail_id=999, current_user_id=2)

    assert "Mail not found!" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_reply_to_mail_success(monkeypatch, capsys) -> None:
    """Tests a successful email reply flow.

    Verifies that a new reply mail is inserted, the original mail status
    is updated to 'REPLIED', and changes are committed.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    monkeypatch.setattr("builtins.input", lambda prompt="": "Sounds good!")

    original_mail = (5, "Meeting Notes")  # sender_id=5, subject="Meeting Notes"
    mock_conn, mock_cur = make_mock_conn(fetchone_return=original_mail)

    with patch("core.crud.update.get_connection", return_value=mock_conn):
        reply_to_mail(mail_id=10, current_user_id=2)

    insert_call = mock_cur.execute.call_args_list[1]
    insert_query, insert_params = insert_call[0]
    assert "INSERT INTO mails" in insert_query
    assert insert_params == (2, 5, "Re: Meeting Notes", "Sounds good!", 10)

    update_call = mock_cur.execute.call_args_list[2]
    update_query, update_params = update_call[0]
    assert "UPDATE mails" in update_query
    assert "status='REPLIED'" in update_query
    assert update_params == (10,)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Reply Sent Successfully!" in capsys.readouterr().out


def test_reply_to_mail_strips_input(monkeypatch) -> None:
    """Tests that leading and trailing whitespace are stripped from the reply body.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    monkeypatch.setattr("builtins.input", lambda prompt="": "  padded reply  ")

    original_mail = (5, "Subject")
    mock_conn, mock_cur = make_mock_conn(fetchone_return=original_mail)

    with patch("core.crud.update.get_connection", return_value=mock_conn):
        reply_to_mail(mail_id=10, current_user_id=2)

    insert_params = mock_cur.execute.call_args_list[1][0][1]
    assert insert_params[3] == "padded reply"