"""Unit tests for the admin user creation functionality.

This test suite uses pytest and unittest.mock to verify the behavior of
`create_user`, including input validation, role validation, email
uniqueness enforcement, the single-CEO rule, password hashing, and
successful account creation.
"""

from unittest.mock import MagicMock, patch

from core.admin.create import create_user


def make_mock_conn(fetchone_return) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchone_return (tuple or None): The value to be returned by the
            mock cursor's `fetchone()` method, representing whether a user
            with the given email already exists.

    Returns:
        tuple: A tuple containing the mock connection object and the mock
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


SAMPLE_ROLES = {
    "EMPLOYEE": {"can_mail": ["MANAGER"], "can_forward": False},
    "MANAGER": {"can_mail": ["EMPLOYEE", "MANAGER", "CEO"], "can_forward": True},
    "CEO": {"can_mail": ["MANAGER"], "can_forward": True},
    "ADMIN": {"can_mail": [], "can_forward": False},
}


# ---------------------------
# input validation
# ---------------------------

def test_create_user_empty_name(capsys) -> None:
    """Tests that user creation fails if the name is empty.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    with patch("core.admin.create.get_connection") as mock_get_conn:
        create_user(
            admin_id=1,
            name="  ",
            email="new@example.com",
            password="pw123",
            role="EMPLOYEE"
        )

    mock_get_conn.assert_not_called()
    assert "Name cannot be empty!" in capsys.readouterr().out


def test_create_user_empty_email(capsys) -> None:
    """Tests that user creation fails if the email is empty.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    with patch("core.admin.create.get_connection") as mock_get_conn:
        create_user(
            admin_id=1,
            name="New User",
            email="   ",
            password="pw123",
            role="EMPLOYEE"
        )

    mock_get_conn.assert_not_called()
    assert "Email cannot be empty!" in capsys.readouterr().out


def test_create_user_empty_password(capsys) -> None:
    """Tests that user creation fails if the password is empty.

    Note the password is intentionally not stripped in the source, so a
    whitespace-only string like " " would NOT trigger this branch — only
    a literal empty string does. This test uses an actual empty string.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    with patch("core.admin.create.get_connection") as mock_get_conn:
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="",
            role="EMPLOYEE"
        )

    mock_get_conn.assert_not_called()
    assert "Password cannot be empty!" in capsys.readouterr().out


def test_create_user_invalid_role(capsys) -> None:
    """Tests that user creation fails if the role isn't a recognized role.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    with patch("core.admin.create.get_connection") as mock_get_conn, \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="pw123",
            role="INTERN"
        )

    mock_get_conn.assert_not_called()

    output = capsys.readouterr().out
    assert "Invalid role!" in output
    assert "EMPLOYEE" in output
    assert "MANAGER" in output
    assert "CEO" in output
    assert "ADMIN" in output


def test_create_user_role_is_case_insensitive(monkeypatch) -> None:
    """Tests that a lowercase role like 'employee' is normalized to 'EMPLOYEE'
    before being validated and inserted, so it's still accepted.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed"):
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="pw123",
            role="employee"
        )

    insert_call = mock_cur.execute.call_args_list[-1]
    _, params = insert_call[0]
    assert params[3] == "EMPLOYEE"


def test_create_user_strips_name_email_role(monkeypatch) -> None:
    """Tests that name, email, and role are stripped of surrounding
    whitespace before validation and insertion.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed"):
        create_user(
            admin_id=1,
            name="  Kimia Rostami  ",
            email="  kimia@company.com  ",
            password="pw123",
            role="  manager  "
        )

    insert_call = mock_cur.execute.call_args_list[-1]
    _, params = insert_call[0]
    assert params == ("Kimia Rostami", "kimia@company.com", "hashed", "MANAGER")


# ---------------------------
# uniqueness enforcement
# ---------------------------

def test_create_user_email_already_exists(capsys) -> None:
    """Tests that user creation aborts if the email is already registered.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=(7,))

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_user(
            admin_id=1,
            name="New User",
            email="taken@example.com",
            password="pw123",
            role="EMPLOYEE"
        )

    assert "already exists" in capsys.readouterr().out
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_user_uniqueness_check_queries_correct_email(monkeypatch) -> None:
    """Tests that the uniqueness check queries the users table filtered by
    the (already-stripped) email address provided.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed"):
        create_user(
            admin_id=1,
            name="New User",
            email="  new@example.com  ",
            password="pw123",
            role="EMPLOYEE"
        )

    select_call = mock_cur.execute.call_args_list[0]
    query, params = select_call[0]
    assert "SELECT" in query
    assert "users" in query
    assert params == ("new@example.com",)


# ---------------------------
# successful creation
# ---------------------------

def test_create_user_success(capsys) -> None:
    """Tests a successful user creation flow.

    Verifies the password is hashed via bcrypt before storage, the correct
    data is inserted into the database, the transaction is committed, and
    connections are closed.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed-pw") as mock_hashpw:
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="plaintext-pw",
            role="EMPLOYEE"
        )

    mock_hashpw.assert_called_once()
    hashed_arg = mock_hashpw.call_args[0][0]
    assert hashed_arg == b"plaintext-pw"

    insert_call = mock_cur.execute.call_args_list[-1]
    query, params = insert_call[0]
    assert "INSERT INTO users" in query
    assert params == ("New User", "new@example.com", "hashed-pw", "EMPLOYEE")

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()

    output = capsys.readouterr().out
    assert "User 'new@example.com' created successfully as EMPLOYEE!" in output


def test_create_user_password_never_stored_in_plaintext(monkeypatch) -> None:
    """Tests that the raw plaintext password never appears in the INSERT
    params — only the bcrypt hash should be stored.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed-pw"):
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="super-secret-123",
            role="EMPLOYEE"
        )

    insert_call = mock_cur.execute.call_args_list[-1]
    _, params = insert_call[0]
    assert "super-secret-123" not in params
    assert "hashed-pw" in params


def test_create_user_is_active_defaults_true_via_query(monkeypatch) -> None:
    """Tests that the INSERT statement hardcodes is_active as TRUE for new
    users (checked via the query text, since it's not a bound parameter).

    Uses a non-CEO role deliberately, so this stays focused on is_active
    only and doesn't also exercise the single-CEO check (see the dedicated
    CEO tests below for that).
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed-pw"):
        create_user(
            admin_id=1,
            name="New User",
            email="new@example.com",
            password="pw123",
            role="EMPLOYEE"
        )

    insert_call = mock_cur.execute.call_args_list[-1]
    query, _ = insert_call[0]
    assert "TRUE" in query


# ---------------------------
# single-CEO rule
# ---------------------------

def test_create_user_ceo_blocked_when_ceo_exists(capsys) -> None:
    """Tests that creating a CEO is rejected if a CEO already exists.

    The rejection is based on any CEO row existing at all (checked via
    `role='CEO'` with no active/inactive filter), so this also covers the
    case where the existing CEO has since been deactivated.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
    mock_cur.fetchone.side_effect = [(1,)]  # COUNT(*) WHERE role='CEO' -> 1 existing

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_user(
            admin_id=1,
            name="Second CEO",
            email="ceo2@example.com",
            password="pw123",
            role="CEO"
        )

    output = capsys.readouterr().out
    assert "CEO already exists" in output

    # Only the CEO-count SELECT should have run — no uniqueness check,
    # and no INSERT.
    assert mock_cur.execute.call_count == 1
    mock_conn.commit.assert_not_called()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_user_ceo_count_query_has_no_active_filter(monkeypatch) -> None:
    """Tests that the CEO-count check counts every CEO row (active or
    deactivated), not just active ones — a deactivated CEO still blocks
    creating a new one.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
    mock_cur.fetchone.side_effect = [(1,)]

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES):
        create_user(
            admin_id=1,
            name="Second CEO",
            email="ceo2@example.com",
            password="pw123",
            role="CEO"
        )

    count_call = mock_cur.execute.call_args_list[0]
    query = count_call[0][0]
    assert "role='CEO'" in query
    assert "is_active" not in query
    # No %s placeholder in this query, so execute() was called with just
    # the query string — no params tuple.
    assert len(count_call[0]) == 1


def test_create_user_ceo_allowed_when_no_ceo_exists(monkeypatch) -> None:
    """Tests that creating a CEO succeeds when no CEO currently exists.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
    mock_cur.fetchone.side_effect = [(0,), None]  # no CEO yet, email not taken

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed"):
        create_user(
            admin_id=1,
            name="First CEO",
            email="ceo@example.com",
            password="pw123",
            role="CEO"
        )

    insert_call = mock_cur.execute.call_args_list[-1]
    query, params = insert_call[0]
    assert "INSERT INTO users" in query
    assert params == ("First CEO", "ceo@example.com", "hashed", "CEO")

    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_user_non_ceo_role_skips_ceo_check(monkeypatch) -> None:
    """Tests that the CEO-count query never runs for non-CEO roles — only
    the uniqueness SELECT and the INSERT should fire.
    """
    mock_conn, mock_cur = make_mock_conn(fetchone_return=None)

    with patch("core.admin.create.get_connection", return_value=mock_conn), \
         patch("core.admin.create.ROLE_PERMISSIONS", SAMPLE_ROLES), \
         patch("core.admin.create.bcrypt.hashpw", return_value=b"hashed"):
        create_user(
            admin_id=1,
            name="New Manager",
            email="manager@example.com",
            password="pw123",
            role="MANAGER"
        )

    assert mock_cur.execute.call_count == 2