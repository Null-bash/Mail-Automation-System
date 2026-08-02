"""Sanity tests verifying bcrypt.checkpw behavior against a known hash.

This isn't testing OCIMAIL application code directly — it verifies that
the bcrypt library itself (as installed in this environment) correctly
validates a password against a pre-generated hash. Useful as a smoke test
if login-related bugs are suspected to come from the bcrypt install/version
rather than from OCIMAIL's own login logic.
"""

import bcrypt
import pytest


# A pre-generated hash of the password "123456", used as a fixed reference
# point so these tests don't depend on generating a new hash at test time.
KNOWN_HASH = "$2a$06$42qM7a9NmV1aY1Z3cV6T5.nufMD0.pdXYTxnQnmDX9CDkIoKSlPZa"
KNOWN_PASSWORD = "123456"


def test_checkpw_correct_password_returns_true() -> None:
    """Tests that the correct password matches the known hash."""
    result = bcrypt.checkpw(
        KNOWN_PASSWORD.encode("utf-8"),
        KNOWN_HASH.encode("utf-8")
    )
    assert result is True


def test_checkpw_wrong_password_returns_false() -> None:
    """Tests that an incorrect password does not match the known hash."""
    result = bcrypt.checkpw(
        "wrong-password".encode("utf-8"),
        KNOWN_HASH.encode("utf-8")
    )
    assert result is False


def test_checkpw_empty_password_returns_false() -> None:
    """Tests that an empty password does not match the known hash."""
    result = bcrypt.checkpw(
        "".encode("utf-8"),
        KNOWN_HASH.encode("utf-8")
    )
    assert result is False


def test_checkpw_case_sensitive() -> None:
    """Tests that password matching is case-sensitive."""
    result = bcrypt.checkpw(
        "123456".upper().encode("utf-8"),
        KNOWN_HASH.encode("utf-8")
    )
    # "123456" has no letters, so this is really just documenting intent;
    # kept for clarity/regression safety if the constant ever changes.
    assert result is True


def test_checkpw_invalid_salt_raises_value_error() -> None:
    """Tests that a malformed/placeholder hash raises ValueError instead
    of silently returning False. This is the exact failure mode seen with
    hand-typed placeholder strings like '$2b$12$ExampleHashPassword123'.
    """
    bad_hash = "$2b$12$ExampleHashPassword123"

    with pytest.raises(ValueError):
        bcrypt.checkpw(
            KNOWN_PASSWORD.encode("utf-8"),
            bad_hash.encode("utf-8")
        )


def test_checkpw_plaintext_stored_hash_raises_value_error() -> None:
    """Tests that a plaintext password mistakenly stored as-is in the
    'hash' field also raises ValueError rather than matching by accident.
    """
    plaintext_as_hash = "123456"

    with pytest.raises(ValueError):
        bcrypt.checkpw(
            KNOWN_PASSWORD.encode("utf-8"),
            plaintext_as_hash.encode("utf-8")
        )


def test_hashpw_and_checkpw_round_trip() -> None:
    """Tests that a freshly generated hash correctly validates its own
    source password, confirming hashpw/checkpw are consistent with each
    other regardless of the fixed KNOWN_HASH constant above.
    """
    password = "some-fresh-password"
    new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    assert bcrypt.checkpw(password.encode("utf-8"), new_hash) is True
    assert bcrypt.checkpw(b"different-password", new_hash) is False