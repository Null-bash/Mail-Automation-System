"""Unit tests for the admin user deactivation functionality.

This test suite uses pytest and unittest.mock to verify the behavior of
`delete_user`, including handling of non-existent users, already-deactivated
users, successful deactivation, and the cascade to that user's own
mail/forward history.
"""

from unittest.mock import MagicMock, patch

from core.admin.delete import delete_user


def make_mock_conn(fetchone_return) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchone_return (tuple or None): The value to be returned by the
            mock cursor's `fetchone()` method, representing the target
            user's current `is_active` status (or None if not found).

    Returns:
        tuple: A tuple containing the mock connection object and the mock
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


def test_delete_user_not_found(capsys) -> None:
    """Tests that deactivation aborts if the target user doesn't exist.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.delete.get_connection", return_value=mock_conn):
        delete_user(admin_id=1, user_id=999)

    assert "User not found!" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_delete_user_already_deactivated(capsys) -> None:
    """Tests that deactivation aborts if the user is already inactive.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(False,))

    with patch("core.admin.delete.get_connection", return_value=mock_conn):
        delete_user(admin_id=1, user_id=5)

    assert "already deactivated" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    mock_conn.commit.assert_not_called()

    # Only the SELECT should have run, no UPDATE
    assert mock_cur.execute.call_count == 1


def test_delete_user_success(capsys) -> None:
    """Tests a successful user deactivation flow.

    Verifies the UPDATE users statement targets the correct user_id, that
    the cascade also flips sender_deleted/receiver_deleted on that user's
    own mails and forwards (all still scoped to the same user_id), that
    everything commits together, and connections are closed.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(True,))

    with patch("core.admin.delete.get_connection", return_value=mock_conn):
        delete_user(admin_id=1, user_id=5)

    calls = mock_cur.execute.call_args_list
    queries = [call[0][0] for call in calls]
    params_list = [call[0][1] for call in calls]

    # 1 SELECT (is_active) + 5 UPDATEs: users, mails x2, forwards x2
    assert mock_cur.execute.call_count == 6

    users_update = next(q for q in queries if "UPDATE users" in q)
    assert "is_active=FALSE" in users_update

    assert any(
        "UPDATE mails" in q and "sender_deleted=TRUE" in q for q in queries
    )
    assert any(
        "UPDATE mails" in q and "receiver_deleted=TRUE" in q for q in queries
    )
    assert any(
        "UPDATE forwards" in q and "sender_deleted=TRUE" in q for q in queries
    )
    assert any(
        "UPDATE forwards" in q and "receiver_deleted=TRUE" in q for q in queries
    )

    # Every query (the initial SELECT and all 5 UPDATEs) is scoped to the
    # same user_id
    assert all(params == (5,) for params in params_list)

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "User deactivated successfully!" in capsys.readouterr().out


def test_delete_user_select_queries_correct_user_id(monkeypatch) -> None:
    """Tests that the initial lookup filters by the given user_id.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(True,))

    with patch("core.admin.delete.get_connection", return_value=mock_conn):
        delete_user(admin_id=1, user_id=42)

    select_call = mock_cur.execute.call_args_list[0]
    query, params = select_call[0]
    assert "SELECT" in query
    assert "is_active" in query
    assert params == (42,)