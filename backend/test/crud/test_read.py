"""Unit tests for email reading and listing operations.

This test suite uses pytest and unittest.mock to verify the behavior of the
read operations including `inbox`, `open_mail`, `sent_mails`, and `via_mail`.
It tests pagination, viewing mail, role-based menu options, and state changes
such as marking emails as seen.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from core.crud.read import inbox, open_mail, sent_mails, via_mail


def make_mock_conn(fetchall_side_effect=None, fetchone_side_effect=None) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchall_side_effect (iterable, optional): A sequence of values to be
            returned sequentially by the mock cursor's `fetchall()` method.
        fetchone_side_effect (iterable, optional): A sequence of values to be
            returned sequentially by the mock cursor's `fetchone()` method.

    Returns:
        tuple: A tuple containing the mock connection object and the mock
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    if fetchall_side_effect is not None:
        mock_cur.fetchall.side_effect = fetchall_side_effect
    if fetchone_side_effect is not None:
        mock_cur.fetchone.side_effect = fetchone_side_effect

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


SAMPLE_DATE = datetime(2026, 1, 15, 10, 30)


# ---------------------------
# inbox
# ---------------------------
# inbox() rows are 7-tuples:
# (id, sender_email, forwarder_email_or_None, subject, status, date, type)

def test_inbox_empty(capsys) -> None:
    """Tests that the inbox correctly reports when it is empty.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[[]])

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        inbox(user_id=1, role="EMPLOYEE")

    assert "Your inbox is empty." in capsys.readouterr().out


def test_inbox_back_immediately(monkeypatch, capsys) -> None:
    """Tests the inbox view and immediately exiting back to the previous menu.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "alice@example.com", None, "Hi", "UNSEEN", SAMPLE_DATE, "MAIL")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        inbox(user_id=1, role="EMPLOYEE")

    output = capsys.readouterr().out
    assert "INBOX" in output
    assert "Hi" in output


def test_inbox_select_mail_calls_open_mail(monkeypatch) -> None:
    """Tests that selecting a specific mail from the inbox calls `open_mail`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    rows = [(42, "alice@example.com", None, "Hi", "UNSEEN", SAMPLE_DATE, "MAIL")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.open_mail") as mock_open_mail:
        inbox(user_id=1, role="EMPLOYEE")

    mock_open_mail.assert_called_once_with(42, "EMPLOYEE", 1)


def test_inbox_select_forward_calls_open_forward(monkeypatch) -> None:
    """Tests that selecting a forwarded item from the inbox calls `open_forward`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    rows = [(7, "creator@example.com", "forwarder@example.com", "FWD Hi", "UNSEEN", SAMPLE_DATE, "FORWARD")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.open_forward") as mock_open_forward:
        inbox(user_id=1, role="MANAGER")

    mock_open_forward.assert_called_once_with(7, "MANAGER", 1)


def test_inbox_pagination_next_then_back(monkeypatch) -> None:
    """Tests inbox pagination logic when navigating to the next page and back.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    page1_rows = [
        (i, f"user{i}@example.com", None, f"Subj {i}", "UNSEEN", SAMPLE_DATE, "MAIL")
        for i in range(11)
    ]
    page2_rows = [(20, "bob@example.com", None, "Last one", "SEEN", SAMPLE_DATE, "MAIL")]

    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[page1_rows, page2_rows])

    inputs = iter(["N", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        inbox(user_id=1, role="EMPLOYEE")

    assert mock_cur.fetchall.call_count == 2
    second_call_args = mock_cur.execute.call_args_list[-1][0][1]
    # query params: (user_id for mails half, user_id for forwards half, limit, offset)
    assert second_call_args == (1, 1, 11, 10)  # offset = page(1) * PAGE_SIZE(10)


def test_inbox_invalid_choice(monkeypatch, capsys) -> None:
    """Tests that the inbox handles invalid user input appropriately.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "alice@example.com", None, "Hi", "UNSEEN", SAMPLE_DATE, "MAIL")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["X", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        inbox(user_id=1, role="EMPLOYEE")

    assert "Invalid Choice!" in capsys.readouterr().out


# ---------------------------
# via_mail
# ---------------------------

def test_via_mail_display_then_back(monkeypatch, capsys) -> None:
    """Tests displaying a sent mail and then returning to the previous menu.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        via_mail(mail_id=1, current_user_id=2)

    output = capsys.readouterr().out
    assert "alice@example.com" in output
    assert "Body" in output


def test_via_mail_delete_calls_delete_mail(monkeypatch) -> None:
    """Tests that deleting a mail from the `via_mail` view calls `delete_mail`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "1")

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.delete_mail") as mock_delete:
        via_mail(mail_id=7, current_user_id=2)

    mock_delete.assert_called_once_with(7, 2)


def test_via_mail_invalid_then_back(monkeypatch, capsys) -> None:
    """Tests handling invalid input within the `via_mail` view.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    inputs = iter(["X", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        via_mail(mail_id=1, current_user_id=2)

    assert "Invalid Choice!" in capsys.readouterr().out


# ---------------------------
# open_mail
# ---------------------------

def test_open_mail_marks_unseen_as_seen(monkeypatch) -> None:
    """Tests that opening an UNSEEN mail correctly updates its status to SEEN.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "UNSEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        open_mail(mail_id=5, role="EMPLOYEE", current_user_id=2)

    update_call = mock_cur.execute.call_args_list[-1]
    query, params = update_call[0]
    assert "SET" in query and "status='SEEN'" in query
    assert params == (5,)
    mock_conn.commit.assert_called_once()


def test_open_mail_already_seen_skips_update(monkeypatch) -> None:
    """Tests that opening an already SEEN mail does not trigger an update query.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        open_mail(mail_id=5, role="EMPLOYEE", current_user_id=2)

    assert mock_cur.execute.call_count == 1  # only the SELECT
    mock_conn.commit.assert_not_called()


def test_open_mail_employee_reply(monkeypatch) -> None:
    """Tests that an employee can select the option to reply to an email.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "1")

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.reply_to_mail") as mock_reply:
        open_mail(mail_id=5, role="EMPLOYEE", current_user_id=2)

    mock_reply.assert_called_once_with(5, 2)


def test_open_mail_employee_delete(monkeypatch) -> None:
    """Tests that an employee can select the option to delete an email.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "2")

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.delete_mail") as mock_delete:
        open_mail(mail_id=5, role="EMPLOYEE", current_user_id=2)

    mock_delete.assert_called_once_with(5, 2)


def test_open_mail_non_employee_forward(monkeypatch) -> None:
    """Tests that non-employees (like managers) have the option to forward email.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "2")

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.forward_mail") as mock_forward:
        open_mail(mail_id=5, role="MANAGER", current_user_id=2)

    mock_forward.assert_called_once_with(5, 2, "MANAGER")


def test_open_mail_non_employee_delete(monkeypatch) -> None:
    """Tests that non-employees can select the option to delete an email.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    monkeypatch.setattr("builtins.input", lambda prompt="": "3")

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.delete_mail") as mock_delete:
        open_mail(mail_id=5, role="MANAGER", current_user_id=2)

    mock_delete.assert_called_once_with(5, 2)


def test_open_mail_invalid_choice(monkeypatch, capsys) -> None:
    """Tests handling invalid input within the `open_mail` view.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mail = ("alice@example.com", "bob@example.com", "Hi", "Body", "SEEN", SAMPLE_DATE)
    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[mail])

    inputs = iter(["X", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        open_mail(mail_id=5, role="EMPLOYEE", current_user_id=2)

    assert "Invalid Choice!" in capsys.readouterr().out


# ---------------------------
# sent_mails
# ---------------------------
# sent_mails() rows are 6-tuples:
# (id, receiver_email, receiver_role, subject, date, type)

def test_sent_mails_empty(capsys) -> None:
    """Tests that the sent mails view correctly reports when it is empty.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[[]])

    with patch("core.crud.read.get_connection", return_value=mock_conn):
        sent_mails(user_id=1, mail_id=None)

    assert "You haven't sent any mails yet." in capsys.readouterr().out


def test_sent_mails_select_calls_via_mail(monkeypatch) -> None:
    """Tests that selecting a specific mail from sent mails calls `via_mail`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    rows = [(99, "bob@example.com", "STAFF", "Hi", SAMPLE_DATE, "MAIL")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.via_mail") as mock_via_mail:
        sent_mails(user_id=1, mail_id=None)

    mock_via_mail.assert_called_once_with(99, 1)


def test_sent_mails_select_forward_calls_via_forward(monkeypatch) -> None:
    """Tests that selecting a forward from sent mails calls `via_forward`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    rows = [(55, "carol@example.com", "MANAGER", "FWD Hi", SAMPLE_DATE, "FORWARD")]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.read.get_connection", return_value=mock_conn), \
         patch("core.crud.read.via_forward") as mock_via_forward:
        sent_mails(user_id=1, mail_id=None)

    mock_via_forward.assert_called_once_with(55, 1)