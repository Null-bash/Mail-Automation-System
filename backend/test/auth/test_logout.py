# test/auth/test_logout.py
from core.auth.logout import logout


def test_logout_clears_session():
    session = {"user": {"id": 1, "name": "alice"}, "token": "abc123"}

    logout(session)

    assert session == {}


def test_logout_prints_message(capsys):
    session = {"user": {"id": 1}}

    logout(session)

    captured = capsys.readouterr()
    assert "Successfully Logged Out!" in captured.out


def test_logout_on_already_empty_session():
    session = {}

    logout(session)

    assert session == {}


def test_logout_does_not_replace_session_object():
    session = {"user": "alice"}
    original_id = id(session)

    logout(session)

    assert id(session) == original_id
    assert session == {}