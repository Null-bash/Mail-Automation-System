"""
Unit tests for the admin user deactivation functionality.

This test suite uses pytest and unittest.mock to verify the behavior of
delete_user, including:

- non-existent users
- already-deactivated users
- ADMIN protection
- successful user deactivation
- soft-deletion of the user's mails
- soft-deletion of the user's forwards
- correct user_id usage
- transaction handling
- database connection cleanup
"""

from unittest.mock import MagicMock, patch

from core.admin.delete import delete_user


def make_mock_conn(fetchone_return):
    """
    Creates and configures mock database connection and cursor objects.

    Args:
        fetchone_return:
            Value returned by cursor.fetchone().

    Returns:
        tuple:
            (mock_conn, mock_cur)
    """

    mock_cur = MagicMock()

    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()

    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


# ============================================================
# USER NOT FOUND
# ============================================================


def test_delete_user_not_found(capsys):
    """
    Deactivation should fail if the target user does not exist.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=None
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=999
        )

    output = capsys.readouterr().out

    assert "User not found!" in output

    mock_cur.close.assert_called_once()

    mock_conn.close.assert_called_once()

    mock_conn.commit.assert_not_called()

    # Only the SELECT should have executed.
    assert mock_cur.execute.call_count == 1


# ============================================================
# ALREADY DELETED
# ============================================================


def test_delete_user_already_deleted(capsys):
    """
    Deactivation should fail if the user is already inactive.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(False, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=5
        )

    output = capsys.readouterr().out

    assert "already deleted" in output

    mock_cur.close.assert_called_once()

    mock_conn.close.assert_called_once()

    mock_conn.commit.assert_not_called()

    # Only the SELECT should execute.
    assert mock_cur.execute.call_count == 1


# ============================================================
# ADMIN PROTECTION
# ============================================================


def test_delete_user_admin_is_not_allowed(capsys):
    """
    ADMIN users cannot be deactivated.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "ADMIN")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=5
        )

    output = capsys.readouterr().out

    assert "Cannot delete an admin user!" in output

    mock_conn.commit.assert_not_called()

    mock_cur.close.assert_called_once()

    mock_conn.close.assert_called_once()

    # Only the initial SELECT should execute.
    assert mock_cur.execute.call_count == 1


# ============================================================
# SUCCESSFUL DEACTIVATION
# ============================================================


def test_delete_user_success(capsys):
    """
    Tests a successful user deactivation.

    The function should:

    1. SELECT the user.
    2. Set users.is_active = FALSE.
    3. Set sender_deleted = TRUE for sent mails.
    4. Set receiver_deleted = TRUE for received mails.
    5. Set sender_deleted = TRUE for sent forwards.
    6. Set receiver_deleted = TRUE for received forwards.
    7. Commit everything.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=5
        )

    calls = mock_cur.execute.call_args_list

    queries = [
        call[0][0]
        for call in calls
    ]

    params_list = [
        call[0][1]
        for call in calls
    ]

    # --------------------------------------------------------
    # SQL execution count
    # --------------------------------------------------------

    # 1 SELECT
    # 1 UPDATE users
    # 2 UPDATE mails
    # 2 UPDATE forwards
    #
    # Total = 6
    assert mock_cur.execute.call_count == 6

    # --------------------------------------------------------
    # users UPDATE
    # --------------------------------------------------------

    users_update = next(
        query
        for query in queries
        if "UPDATE users" in query
    )

    assert "is_active=FALSE" in users_update

    # --------------------------------------------------------
    # mails UPDATEs
    # --------------------------------------------------------

    sender_mail_update = next(
        query
        for query in queries
        if (
            "UPDATE mails" in query
            and "sender_deleted=TRUE" in query
        )
    )

    receiver_mail_update = next(
        query
        for query in queries
        if (
            "UPDATE mails" in query
            and "receiver_deleted=TRUE" in query
        )
    )

    assert "sender_id=%s" in sender_mail_update

    assert "receiver_id=%s" in receiver_mail_update

    # --------------------------------------------------------
    # forwards UPDATEs
    # --------------------------------------------------------

    sender_forward_update = next(
        query
        for query in queries
        if (
            "UPDATE forwards" in query
            and "sender_deleted=TRUE" in query
        )
    )

    receiver_forward_update = next(
        query
        for query in queries
        if (
            "UPDATE forwards" in query
            and "receiver_deleted=TRUE" in query
        )
    )

    assert "sender_id=%s" in sender_forward_update

    assert "receiver_id=%s" in receiver_forward_update

    # --------------------------------------------------------
    # user_id parameters
    # --------------------------------------------------------

    assert all(
        params == (5,)
        for params in params_list
    )

    # --------------------------------------------------------
    # transaction
    # --------------------------------------------------------

    mock_conn.commit.assert_called_once()

    # --------------------------------------------------------
    # cleanup
    # --------------------------------------------------------

    mock_cur.close.assert_called_once()

    mock_conn.close.assert_called_once()

    # --------------------------------------------------------
    # output
    # --------------------------------------------------------

    output = capsys.readouterr().out

    assert "User deleted successfully!" in output


# ============================================================
# SELECT QUERY
# ============================================================


def test_delete_user_select_queries_correct_user_id():
    """
    The initial SELECT should use the supplied user_id.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=42
        )

    select_call = mock_cur.execute.call_args_list[0]

    query, params = select_call[0]

    assert "SELECT" in query

    assert "is_active" in query

    assert "role" in query

    assert "users" in query

    assert "user_id=%s" in query

    assert params == (42,)


# ============================================================
# MAIL CASCADE
# ============================================================


def test_delete_user_cascades_to_sent_mails():
    """
    Deactivating a user should mark all mails sent by that user
    as sender_deleted.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=42
        )

    queries = [
        call[0][0]
        for call in mock_cur.execute.call_args_list
    ]

    sender_mail_queries = [
        query
        for query in queries
        if (
            "UPDATE mails" in query
            and "sender_deleted=TRUE" in query
        )
    ]

    assert len(sender_mail_queries) == 1

    assert "sender_id=%s" in sender_mail_queries[0]


def test_delete_user_cascades_to_received_mails():
    """
    Deactivating a user should mark all mails received by that user
    as receiver_deleted.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=42
        )

    queries = [
        call[0][0]
        for call in mock_cur.execute.call_args_list
    ]

    receiver_mail_queries = [
        query
        for query in queries
        if (
            "UPDATE mails" in query
            and "receiver_deleted=TRUE" in query
        )
    ]

    assert len(receiver_mail_queries) == 1

    assert "receiver_id=%s" in receiver_mail_queries[0]


# ============================================================
# FORWARD CASCADE
# ============================================================


def test_delete_user_cascades_to_sent_forwards():
    """
    Deactivating a user should mark forwards sent by that user
    as sender_deleted.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=42
        )

    queries = [
        call[0][0]
        for call in mock_cur.execute.call_args_list
    ]

    sender_forward_queries = [
        query
        for query in queries
        if (
            "UPDATE forwards" in query
            and "sender_deleted=TRUE" in query
        )
    ]

    assert len(sender_forward_queries) == 1

    assert "sender_id=%s" in sender_forward_queries[0]


def test_delete_user_cascades_to_received_forwards():
    """
    Deactivating a user should mark forwards received by that user
    as receiver_deleted.
    """

    mock_conn, mock_cur = make_mock_conn(
        fetchone_return=(True, "EMPLOYEE")
    )

    with patch(
        "core.admin.delete.get_connection",
        return_value=mock_conn
    ):

        delete_user(
            admin_id=1,
            user_id=42
        )

    queries = [
        call[0][0]
        for call in mock_cur.execute.call_args_list
    ]

    receiver_forward_queries = [
        query
        for query in queries
        if (
            "UPDATE forwards" in query
            and "receiver_deleted=TRUE" in query
        )
    ]

    assert len(receiver_forward_queries) == 1

    assert "receiver_id=%s" in receiver_forward_queries[0]