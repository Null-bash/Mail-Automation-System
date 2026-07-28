"""Unit tests for the email creation and forwarding operations.

This test suite uses pytest and unittest.mock to verify the behavior of the
`create_mail` and `forward_mail` functions. It tests input validation,
database interactions, business rules (like not emailing oneself), and
role-based access control permissions.
"""

from unittest.mock import MagicMock, patch

from core.crud.create import create_mail, forward_mail


def make_mock_conn(fetchone_side_effect) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Configures the `fetchone` method to use a side_effect, which allows 
    returning a sequence of different values for consecutive database queries.

    Args:
        fetchone_side_effect (iterable): A list or sequence of values (or exceptions)
            to be returned sequentially by the mock cursor's `fetchone()` method.

    Returns:
        tuple: A tuple containing the mock connection object and the mock 
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = fetchone_side_effect

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


SAMPLE_ROLES = {
    "admin": {"can_mail": ["admin", "staff", "user"], "can_forward": True},
    "staff": {"can_mail": ["staff", "user"], "can_forward": True},
    "user": {"can_mail": [], "can_forward": False},
}


# ---------------------------
# create_mail
# ---------------------------

def test_create_mail_empty_receiver_email(monkeypatch, capsys) -> None:
    """Tests that mail creation fails if the receiver email is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.create.get_connection") as mock_get_conn:
        create_mail(sender_id=1, sender_role="admin")

    mock_get_conn.assert_not_called()
    assert "Receiver Email cannot be empty!" in capsys.readouterr().out


def test_create_mail_empty_subject(monkeypatch, capsys) -> None:
    """Tests that mail creation fails if the subject is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.create.get_connection") as mock_get_conn:
        create_mail(sender_id=1, sender_role="admin")

    mock_get_conn.assert_not_called()
    assert "Subject cannot be empty!" in capsys.readouterr().out


def test_create_mail_empty_body(monkeypatch, capsys) -> None:
    """Tests that mail creation fails if the body is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", "Hello", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.create.get_connection") as mock_get_conn:
        create_mail(sender_id=1, sender_role="admin")

    mock_get_conn.assert_not_called()
    assert "Body cannot be empty!" in capsys.readouterr().out


def test_create_mail_receiver_does_not_exist(monkeypatch, capsys) -> None:
    """Tests that mail creation aborts if the specified receiver does not exist.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["ghost@example.com", "Hi", "Body text"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[None])

    with patch("core.crud.create.get_connection", return_value=mock_conn):
        create_mail(sender_id=1, sender_role="admin")

    assert "Receiver does not exist!" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_mail_cannot_send_to_self(monkeypatch, capsys) -> None:
    """Tests the business rule preventing users from emailing themselves.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["me@example.com", "Hi", "Body text"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[(1, "admin")])

    with patch("core.crud.create.get_connection", return_value=mock_conn):
        create_mail(sender_id=1, sender_role="admin")

    assert "cannot send a mail to yourself" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_mail_permission_denied(monkeypatch, capsys) -> None:
    """Tests role-based access control preventing unauthorized mail creation.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["user@example.com", "Hi", "Body text"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[(2, "admin")])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_mail(sender_id=1, sender_role="user")

    assert "don't have permission" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_mail_success(monkeypatch, capsys) -> None:
    """Tests a successful email creation flow.

    Verifies that the correct data is inserted into the database and changes 
    are properly committed when all inputs and permissions are valid.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", "Hi", "Body text"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[(2, "staff")])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_mail(sender_id=1, sender_role="admin")

    insert_call = mock_cur.execute.call_args_list[-1]
    query, params = insert_call[0]
    assert "INSERT INTO mails" in query
    assert params == (1, 2, "Hi", "Body text")

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Mail Sent Successfully!" in capsys.readouterr().out


# ---------------------------
# forward_mail
# ---------------------------

def test_forward_mail_no_permission(monkeypatch, capsys) -> None:
    """Tests that forwarding aborts if the sender's role lacks the capability.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    with patch("core.crud.create.get_connection") as mock_get_conn, \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=1, sender_id=1, sender_role="user")

    mock_get_conn.assert_not_called()
    assert "don't have permission to forward mails!" in capsys.readouterr().out


def test_forward_mail_empty_receiver_email(monkeypatch, capsys) -> None:
    """Tests that forwarding aborts if the new receiver email is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.crud.create.get_connection") as mock_get_conn, \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=1, sender_id=1, sender_role="admin")

    mock_get_conn.assert_not_called()
    assert "Receiver Email cannot be empty!" in capsys.readouterr().out


def test_forward_mail_receiver_does_not_exist(monkeypatch, capsys) -> None:
    """Tests that forwarding aborts if the new receiver does not exist.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["ghost@example.com", "note"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[None])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=1, sender_id=1, sender_role="admin")

    assert "Receiver does not exist!" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_forward_mail_cannot_forward_to_original_sender(monkeypatch, capsys) -> None:
    """Tests the rule preventing forwarding a mail back to its original sender.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", "note"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[
        (2, "staff"),   # receiver lookup
        (2,),           # original sender lookup -> same as receiver_id
    ])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=99, sender_id=1, sender_role="admin")

    assert "back to its original sender" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_forward_mail_cannot_forward_to_self(monkeypatch, capsys) -> None:
    """Tests the rule preventing users from forwarding an email to themselves.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", "note"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[
        (1, "staff"),   # receiver lookup -> same as sender_id
        (5,),           # original sender lookup
    ])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=99, sender_id=1, sender_role="admin")

    output = capsys.readouterr().out
    assert "cannot forward a mail" in output
    assert "to yourself" in output
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_forward_mail_permission_denied_for_role(monkeypatch, capsys) -> None:
    """Tests role-based restrictions on who a user can forward emails to.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["admin@example.com", "note"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[
        (2, "admin"),   # receiver lookup: "admin" not in staff's can_mail
        (5,),           # original sender lookup
    ])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=99, sender_id=1, sender_role="staff")

    output = capsys.readouterr().out
    assert "don't have permission to forward to this role!" in output
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_forward_mail_success(monkeypatch, capsys) -> None:
    """Tests a successful email forwarding flow.

    Verifies that the new forwarded email is inserted into the `mails` table,
    the forwarding relationship is logged in the `forwards` table, and 
    changes are properly committed to the database.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    inputs = iter(["bob@example.com", "fyi"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    mock_conn, mock_cur = make_mock_conn(fetchone_side_effect=[
        (2, "staff"),          # receiver lookup
        (5,),                  # original sender lookup
        ("Hello", "Body text"),  # original mail lookup
        (42,),                 # new_mail_id from RETURNING
    ])

    with patch("core.crud.create.get_connection", return_value=mock_conn), \
         patch("core.crud.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        forward_mail(mail_id=99, sender_id=1, sender_role="admin")

    insert_mail_call = mock_cur.execute.call_args_list[-2]
    query, params = insert_mail_call[0]
    assert "INSERT INTO mails" in query
    assert params == (1, 2, "FWD: Hello", "Body text")

    insert_forward_call = mock_cur.execute.call_args_list[-1]
    query2, params2 = insert_forward_call[0]
    assert "INSERT INTO forwards" in query2
    assert params2 == (1, 2, "fyi", 42)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Mail forwarded successfully!" in capsys.readouterr().out