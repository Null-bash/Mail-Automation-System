"""Unit tests for the user menu operations.

This test suite uses pytest and unittest.mock to verify the behavior of the
`user_menu` function. It tests menu option routing (creating mail, checking
inbox, viewing sent mails, logging out), handling of invalid inputs, and
proper display of user welcome messages and roles.
"""

from unittest.mock import MagicMock, patch

from core.menus.user_menu import user_menu


def make_session(user) -> dict:
    """Creates a mock user session dictionary.

    Args:
        user (tuple): A tuple containing user session details.

    Returns:
        dict: A dictionary containing the user session data.
    """
    return {"user": user}


SAMPLE_USER = (1, "Alice", "alice@example.com", "hash", "ADMIN")


def test_user_menu_create_mail(monkeypatch) -> None:
    """Tests that selecting the create mail option calls `create_mail` and logs out.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    session = make_session(SAMPLE_USER)

    inputs = iter(["1", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.create_mail") as mock_create, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_create.assert_called_once_with(1, "ADMIN")
    mock_logout.assert_called_once_with(session)


def test_user_menu_inbox(monkeypatch) -> None:
    """Tests that selecting the inbox option calls `inbox` and logs out.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    session = make_session(SAMPLE_USER)

    inputs = iter(["2", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.inbox") as mock_inbox, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_inbox.assert_called_once_with(1, "ADMIN")
    mock_logout.assert_called_once_with(session)


def test_user_menu_sent_mails(monkeypatch) -> None:
    """Tests that selecting the sent mails option calls `sent_mails` and logs out.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    session = make_session(SAMPLE_USER)

    inputs = iter(["3", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.sent_mails") as mock_sent, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=42)

    mock_sent.assert_called_once_with(1, 42)
    mock_logout.assert_called_once_with(session)


def test_user_menu_logout_breaks_loop(monkeypatch) -> None:
    """Tests that selecting the logout option breaks the menu loop and calls `logout`.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
    """
    session = make_session(SAMPLE_USER)

    monkeypatch.setattr("builtins.input", lambda prompt="": "4")

    with patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_logout.assert_called_once_with(session)


def test_user_menu_invalid_choice(monkeypatch, capsys) -> None:
    """Tests that entering an invalid menu choice prints an error message and logs out.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    session = make_session(SAMPLE_USER)

    inputs = iter(["9", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    assert "Invalid Choice!" in capsys.readouterr().out
    mock_logout.assert_called_once_with(session)


def test_user_menu_displays_welcome_and_role(monkeypatch, capsys) -> None:
    """Tests that the user menu correctly displays the user's name and role on startup.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to mock standard input.
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    session = make_session(SAMPLE_USER)

    monkeypatch.setattr("builtins.input", lambda prompt="": "4")

    with patch("core.menus.user_menu.logout"):
        user_menu(session, mail_id=None)

    output = capsys.readouterr().out
    assert "Welcome Alice" in output
    assert "Role: ADMIN" in output