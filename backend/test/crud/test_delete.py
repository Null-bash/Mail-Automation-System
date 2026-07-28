# test/crud/test_delete.py
from unittest.mock import patch, MagicMock
import pytest
from core.crud.delete import delete_mail


def make_mock_conn(fetchone_return):
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


def test_delete_mail_sender_deletes(capsys):
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


def test_delete_mail_receiver_deletes(capsys):
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


def test_delete_mail_unrelated_user_still_commits_and_prints_success(capsys):
    """
    Documents current behavior: if current_user_id is neither sender nor
    receiver, no UPDATE runs, but commit() still happens and the success
    message still prints. This may be a bug worth fixing in delete_mail().
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


def test_delete_mail_nonexistent_mail_raises(capsys):
    """
    Documents current behavior: if mail_id doesn't exist, fetchone()
    returns None, and mail[0] raises TypeError. Connection is never
    closed in this path (leak).
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.crud.delete.get_connection", return_value=mock_conn):
        with pytest.raises(TypeError):
            delete_mail(mail_id=999, current_user_id=1)

    mock_cur.close.assert_not_called()
    mock_conn.close.assert_not_called()