# test/menus/test_user_menu.py
from unittest.mock import patch, MagicMock
from core.menus.user_menu import user_menu


def make_session(user):
    return {"user": user}


SAMPLE_USER = (1, "Alice", "alice@example.com", "hash", "ADMIN")


def test_user_menu_create_mail(monkeypatch):
    session = make_session(SAMPLE_USER)

    inputs = iter(["1", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.create_mail") as mock_create, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_create.assert_called_once_with(1, "ADMIN")
    mock_logout.assert_called_once_with(session)


def test_user_menu_inbox(monkeypatch):
    session = make_session(SAMPLE_USER)

    inputs = iter(["2", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.inbox") as mock_inbox, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_inbox.assert_called_once_with(1, "ADMIN")
    mock_logout.assert_called_once_with(session)


def test_user_menu_sent_mails(monkeypatch):
    session = make_session(SAMPLE_USER)

    inputs = iter(["3", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.sent_mails") as mock_sent, \
         patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=42)

    mock_sent.assert_called_once_with(1, 42)
    mock_logout.assert_called_once_with(session)


def test_user_menu_logout_breaks_loop(monkeypatch):
    session = make_session(SAMPLE_USER)

    monkeypatch.setattr("builtins.input", lambda prompt="": "4")

    with patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    mock_logout.assert_called_once_with(session)


def test_user_menu_invalid_choice(monkeypatch, capsys):
    session = make_session(SAMPLE_USER)

    inputs = iter(["9", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("core.menus.user_menu.logout") as mock_logout:
        user_menu(session, mail_id=None)

    assert "Invalid Choice!" in capsys.readouterr().out
    mock_logout.assert_called_once_with(session)


def test_user_menu_displays_welcome_and_role(monkeypatch, capsys):
    session = make_session(SAMPLE_USER)

    monkeypatch.setattr("builtins.input", lambda prompt="": "4")

    with patch("core.menus.user_menu.logout"):
        user_menu(session, mail_id=None)

    output = capsys.readouterr().out
    assert "Welcome Alice" in output
    assert "Role: ADMIN" in output