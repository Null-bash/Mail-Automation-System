"""Unit tests for the admin user listing functionality.

This test suite uses pytest and unittest.mock to verify the behavior of
`list_users`, including empty results, pagination (Next/Previous), display
formatting, and handling invalid menu input.
"""

from unittest.mock import MagicMock, patch

from core.admin.read import list_users


def make_mock_conn(fetchall_side_effect) -> tuple:
    """Creates and configures mock database connection and cursor objects.

    Args:
        fetchall_side_effect (iterable): A sequence of values to be returned
            sequentially by the mock cursor's `fetchall()` method,
            representing successive pages of user rows.

    Returns:
        tuple: A tuple containing the mock connection object and the mock
            cursor object `(mock_conn, mock_cur)`.
    """
    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = fetchall_side_effect

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


def test_list_users_empty(capsys) -> None:
    """Tests that the listing correctly reports when there are no users.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[[]])

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert "No users found." in capsys.readouterr().out


def test_list_users_back_immediately(monkeypatch, capsys) -> None:
    """Tests the listing view and immediately exiting back to the previous menu.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "Alice", "alice@example.com", "EMPLOYEE", True)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    output = capsys.readouterr().out
    assert "USERS" in output
    assert "Alice (alice@example.com)" in output
    assert "ID     : 1" in output
    assert "Role   : EMPLOYEE" in output
    assert "Status : ACTIVE" in output


def test_list_users_shows_deactivated_status(monkeypatch, capsys) -> None:
    """Tests that inactive users are displayed with a DEACTIVATED status.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(2, "Bob", "bob@example.com", "MANAGER", False)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert "Status : DELETED" in capsys.readouterr().out


def test_list_users_pagination_next_then_back(monkeypatch) -> None:
    """Tests pagination logic when navigating to the next page and back.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    page1_rows = [
        (i, f"User{i}", f"user{i}@example.com", "EMPLOYEE", True)
        for i in range(11)
    ]
    page2_rows = [(20, "Last", "last@example.com", "CEO", True)]

    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[page1_rows, page2_rows])

    inputs = iter(["N", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert mock_cur.fetchall.call_count == 2
    second_call_args = mock_cur.execute.call_args_list[-1][0][1]
    assert second_call_args == (11, 10)  # limit = PAGE_SIZE+1, offset = page(1) * PAGE_SIZE(10)


def test_list_users_previous_not_shown_on_first_page(monkeypatch, capsys) -> None:
    """Tests that the 'Previous' option isn't shown when already on page 0.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "Alice", "alice@example.com", "EMPLOYEE", True)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert "P. Previous" not in capsys.readouterr().out


def test_list_users_next_not_shown_when_no_more_pages(monkeypatch, capsys) -> None:
    """Tests that the 'Next' option isn't shown when there are no further pages.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "Alice", "alice@example.com", "EMPLOYEE", True)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows])

    monkeypatch.setattr("builtins.input", lambda prompt="": "0")

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert "N. Next" not in capsys.readouterr().out


def test_list_users_invalid_choice(monkeypatch, capsys) -> None:
    """Tests that invalid menu input is handled without crashing.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    rows = [(1, "Alice", "alice@example.com", "EMPLOYEE", True)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["X", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    assert "Invalid Choice!" in capsys.readouterr().out


def test_list_users_previous_ignored_on_first_page(monkeypatch) -> None:
    """Tests that pressing 'P' on the first page doesn't decrement below 0
    or re-query with a negative offset (falls through to invalid choice
    handling since the 'P' branch requires page > 0).
    """
    rows = [(1, "Alice", "alice@example.com", "EMPLOYEE", True)]
    mock_conn, mock_cur = make_mock_conn(fetchall_side_effect=[rows, rows])

    inputs = iter(["P", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.admin.read.get_connection", return_value=mock_conn):
        list_users(admin_id=1)

    # Only two fetches: initial page 0, then page 0 again after invalid 'P'
    assert mock_cur.fetchall.call_count == 2
    last_offset = mock_cur.execute.call_args_list[-1][0][1][1]
    assert last_offset == 0