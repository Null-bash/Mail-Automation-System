"""Unit tests for the authentication logout module.

This test suite verifies the behavior of the logout process, ensuring that
user sessions are properly cleared in place and the appropriate confirmation
messages are displayed.
"""

from core.auth.logout import logout


def test_logout_clears_session() -> None:
    """Tests that the session dictionary is completely cleared.

    Populates a mock session dictionary with user data and a token,
    executes the logout function, and asserts that the dictionary
    is empty afterwards.
    """
    session = {"user": {"id": 1, "name": "alice"}, "token": "abc123"}

    logout(session)

    assert session == {}


def test_logout_prints_message(capsys) -> None:
    """Tests that the correct confirmation message is printed on logout.

    Args:
        capsys (pytest.CaptureFixture): Pytest fixture to capture stdout/stderr.
    """
    session = {"user": {"id": 1}}

    logout(session)

    captured = capsys.readouterr()
    assert "Successfully Logged Out!" in captured.out


def test_logout_on_already_empty_session() -> None:
    """Tests logout behavior when the session is already empty.

    Ensures that calling logout on an empty dictionary does not raise
    any exceptions and leaves the dictionary empty.
    """
    session = {}

    logout(session)

    assert session == {}


def test_logout_does_not_replace_session_object() -> None:
    """Tests that the session dictionary is cleared in-place.

    Verifies that the original dictionary object is modified (using `clear()`)
    rather than being reassigned to a new empty dictionary, ensuring references
    to the session object remain valid across the application.
    """
    session = {"user": "alice"}
    original_id = id(session)

    logout(session)

    assert id(session) == original_id
    assert session == {}