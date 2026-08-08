"""Unit tests for the email and forward deletion operations.

This test suite uses pytest and unittest.mock to verify the behavior of the
`delete_mail` and `delete_forward` functions. It tests deletion by the
sender, deletion by the receiver, and documents current edge cases such as
unauthorized deletion attempts and handling of non-existent records.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.crud.delete import delete_mail, delete_forward


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


# ---------------------------
# delete_mail
# ---------------------------

def test_delete_mail_sender_deletes(capsys) -> None:
    """Tests that a mail is marked as sender_deleted when the sender deletes it.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))  # sender_id=1, receiver_id=2

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_mail(mail_id=10, current_user_id=1)

    update_call = mock_cur.execute.call_args_list[-1]
    query, params = update_call[0]
    assert "sender_deleted" in query
    assert params == (10,)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Mail Deleted Successfully!" in capsys.readouterr().out


def test_delete_mail_receiver_deletes(capsys) -> None:
    """Tests that a mail is marked as receiver_deleted when the receiver deletes it.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))  # sender_id=1, receiver_id=2

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_mail(mail_id=10, current_user_id=2)

    update_call = mock_cur.execute.call_args_list[-1]
    query, params = update_call[0]
    assert "receiver_deleted" in query
    assert params == (10,)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Mail Deleted Successfully!" in capsys.readouterr().out


def test_delete_mail_unrelated_user_still_commits_and_prints_success(capsys) -> None:
    """Tests current behavior when an unrelated user attempts to delete a mail.

    Documents current behavior: if `current_user_id` is neither sender nor
    receiver, no UPDATE runs, but `commit()` still happens and the success
    message still prints. This may be a bug worth fixing in `delete_mail()`.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_mail(mail_id=10, current_user_id=999)

    # only the SELECT ran, no UPDATE
    assert mock_cur.execute.call_count == 1

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Mail Deleted Successfully!" in capsys.readouterr().out


def test_delete_mail_nonexistent_mail_raises(capsys) -> None:
    """Tests current behavior when attempting to delete a nonexistent mail.

    Documents current behavior: if `mail_id` doesn't exist, `fetchone()`
    returns None, and `mail[0]` raises a TypeError. The database connection
    is never closed in this path (potential leak).

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        with pytest.raises(TypeError):
            delete_mail(mail_id=999, current_user_id=1)

    mock_cur.close.assert_not_called()
    mock_conn.close.assert_not_called()


# ---------------------------
# delete_forward
# ---------------------------

def test_delete_forward_sender_deletes(capsys) -> None:
    """Tests that a forward is marked as sender_deleted when its sender deletes it.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))  # sender_id=1, receiver_id=2

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_forward(forward_id=10, current_user_id=1)

    update_call = mock_cur.execute.call_args_list[-1]
    query, params = update_call[0]
    assert "sender_deleted" in query
    assert params == (10,)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Forward Deleted Successfully!" in capsys.readouterr().out


def test_delete_forward_receiver_deletes(capsys) -> None:
    """Tests that a forward is marked as receiver_deleted when its receiver deletes it.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))  # sender_id=1, receiver_id=2

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_forward(forward_id=10, current_user_id=2)

    update_call = mock_cur.execute.call_args_list[-1]
    query, params = update_call[0]
    assert "receiver_deleted" in query
    assert params == (10,)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Forward Deleted Successfully!" in capsys.readouterr().out


def test_delete_forward_unrelated_user_still_commits_and_prints_success(capsys) -> None:
    """Tests current behavior when an unrelated user attempts to delete a forward.

    Documents current behavior: if `current_user_id` is neither the
    forward's sender nor receiver, no UPDATE runs, but `commit()` still
    happens and the success message still prints — the same pattern as
    `delete_mail`, since `delete_forward` was written to mirror its style.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(1, 2))

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        delete_forward(forward_id=10, current_user_id=999)

    # only the SELECT ran, no UPDATE
    assert mock_cur.execute.call_count == 1

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Forward Deleted Successfully!" in capsys.readouterr().out


def test_delete_forward_nonexistent_forward_raises(capsys) -> None:
    """Tests current behavior when attempting to delete a nonexistent forward.

    Documents current behavior: if `forward_id` doesn't exist, `fetchone()`
    returns None, and `forward[0]` raises a TypeError. The database
    connection is never closed in this path (potential leak) — the same
    latent issue as `delete_mail`.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        with pytest.raises(TypeError):
            delete_forward(forward_id=999, current_user_id=1)

    mock_cur.close.assert_not_called()
    mock_conn.close.assert_not_called()