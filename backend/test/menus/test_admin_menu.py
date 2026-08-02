"""Tests for core.menus.admin_menu.

Covers menu navigation, dispatch to create/list/delete user actions,
input validation for the delete flow, and loop/exit behavior.
"""

from unittest.mock import patch, call

import pytest

from core.menus.admin_menu import admin_menu


@pytest.fixture
def session():
    """A minimal session dict shaped like the real app produces it.

    Index 0 of the user tuple is treated as the admin's user_id.
    """
    return {"user": ("admin-id-123", "Admin Name", "admin@company.com", "hash", "ADMIN")}


class TestAdminMenuLogout:

    def test_logout_immediately_returns(self, session):
        """Choosing '0' right away should exit the loop without any action."""
        with patch("builtins.input", side_effect=["0"]):
            result = admin_menu(session)

        assert result is None


class TestAdminMenuCreateUser:

    def test_create_user_dispatches_with_collected_fields(self, session):
        """Choice '1' should prompt for all fields and call create_user
        with the admin_id plus the exact values entered, role uppercased.
        """
        inputs = [
            "1",
            "Kimia Rostami",
            "kimia@company.com",
            "supersecret",
            "employee",
            "0",
        ]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.create_user") as mock_create_user:

            admin_menu(session)

        mock_create_user.assert_called_once_with(
            "admin-id-123",
            "Kimia Rostami",
            "kimia@company.com",
            "supersecret",
            "EMPLOYEE",
        )

    def test_create_user_strips_whitespace(self, session):
        """Leading/trailing whitespace on each field should be stripped
        before being passed to create_user.
        """
        inputs = [
            "1",
            "  Reza  ",
            "  reza@test.com  ",
            "  pw123  ",
            "  manager  ",
            "0",
        ]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.create_user") as mock_create_user:

            admin_menu(session)

        mock_create_user.assert_called_once_with(
            "admin-id-123",
            "Reza",
            "reza@test.com",
            "pw123",
            "MANAGER",
        )


class TestAdminMenuListUsers:

    def test_list_users_dispatches_with_admin_id(self, session):
        """Choice '2' should call list_users with just the admin_id."""
        inputs = ["2", "0"]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.list_users") as mock_list_users:

            admin_menu(session)

        mock_list_users.assert_called_once_with("admin-id-123")


class TestAdminMenuDeleteUser:

    def test_delete_user_dispatches_with_valid_id(self, session):
        """Choice '3' with a non-empty user id should call delete_user
        with the admin_id and the entered (stripped) target id.
        """
        inputs = ["3", " target-id-456 ", "0"]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.delete_user") as mock_delete_user:

            admin_menu(session)

        mock_delete_user.assert_called_once_with(
            "admin-id-123",
            "target-id-456",
        )

    def test_delete_user_rejects_empty_id(self, session, capsys):
        """An empty user id input should print an error, skip calling
        delete_user, and loop back to the menu instead of crashing.
        """
        inputs = ["3", "", "0"]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.delete_user") as mock_delete_user:

            admin_menu(session)

        mock_delete_user.assert_not_called()

        captured = capsys.readouterr()
        assert "Invalid User ID!" in captured.out

    def test_delete_user_rejects_whitespace_only_id(self, session):
        """Whitespace-only input should be treated the same as empty,
        since it's stripped before the emptiness check.
        """
        inputs = ["3", "   ", "0"]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.delete_user") as mock_delete_user:

            admin_menu(session)

        mock_delete_user.assert_not_called()


class TestAdminMenuInvalidChoice:

    def test_invalid_choice_prints_error_and_continues(self, session, capsys):
        """An unrecognized choice should print an error and loop back
        to the menu rather than exiting or raising.
        """
        inputs = ["9", "0"]

        with patch("builtins.input", side_effect=inputs):
            admin_menu(session)

        captured = capsys.readouterr()
        assert "Invalid Choice!" in captured.out

    def test_empty_choice_treated_as_invalid(self, session, capsys):
        """An empty string input (just pressing Enter) should also be
        treated as an invalid choice, not crash.
        """
        inputs = ["", "0"]

        with patch("builtins.input", side_effect=inputs):
            admin_menu(session)

        captured = capsys.readouterr()
        assert "Invalid Choice!" in captured.out


class TestAdminMenuLoopBehavior:

    def test_multiple_actions_before_logout(self, session):
        """The menu should support multiple actions in sequence within
        the same session before finally logging out.
        """
        inputs = [
            "2",              # list users
            "3", "id-1",      # delete user
            "1", "Name", "e@x.com", "pw", "ceo",  # create user
            "0",              # logout
        ]

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.list_users") as mock_list_users, \
             patch("core.menus.admin_menu.delete_user") as mock_delete_user, \
             patch("core.menus.admin_menu.create_user") as mock_create_user:

            admin_menu(session)

        mock_list_users.assert_called_once_with("admin-id-123")
        mock_delete_user.assert_called_once_with("admin-id-123", "id-1")
        mock_create_user.assert_called_once_with(
            "admin-id-123", "Name", "e@x.com", "pw", "CEO"
        )

    def test_stops_prompting_after_exhausted_inputs_raises_stopiteration(self, session):
        """Sanity check: if the loop never receives '0' and inputs run
        out, StopIteration propagates — confirming the loop truly keeps
        prompting rather than exiting on its own after one iteration.
        """
        inputs = ["2"]  # no logout choice provided

        with patch("builtins.input", side_effect=inputs), \
             patch("core.menus.admin_menu.list_users"):

            with pytest.raises(StopIteration):
                admin_menu(session)