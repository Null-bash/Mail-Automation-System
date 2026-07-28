"""Unit tests for role-based permissions configuration.

This test suite uses pytest to verify the structure, completeness, and correctness
of the `ROLE_PERMISSIONS` configuration dictionary. It checks that all expected roles
are present, required keys exist, permission types are valid, and specific business
rules (such as chain-of-command restrictions) are enforced.
"""

from core.permissions.roles import ROLE_PERMISSIONS


def test_all_expected_roles_present() -> None:
    """Tests that exactly the expected set of roles are defined in `ROLE_PERMISSIONS`."""
    assert set(ROLE_PERMISSIONS.keys()) == {"EMPLOYEE", "MANAGER", "CEO"}


def test_every_role_has_required_keys() -> None:
    """Tests that every role definition contains the mandatory permission keys."""
    for role, perms in ROLE_PERMISSIONS.items():
        assert "can_mail" in perms, f"{role} missing 'can_mail'"
        assert "can_forward" in perms, f"{role} missing 'can_forward'"


def test_can_mail_values_are_lists_of_valid_roles() -> None:
    """Tests that `can_mail` values are lists containing only valid role names."""
    valid_roles = set(ROLE_PERMISSIONS.keys())
    for role, perms in ROLE_PERMISSIONS.items():
        assert isinstance(perms["can_mail"], list), f"{role}'s can_mail should be a list"
        for target in perms["can_mail"]:
            assert target in valid_roles, f"{role} can_mail references unknown role '{target}'"


def test_can_forward_values_are_booleans() -> None:
    """Tests that `can_forward` values are properly typed as booleans."""
    for role, perms in ROLE_PERMISSIONS.items():
        assert isinstance(perms["can_forward"], bool), f"{role}'s can_forward should be a bool"


def test_employee_permissions() -> None:
    """Tests specific permission mappings configured for the EMPLOYEE role."""
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_mail"] == ["MANAGER"]
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_forward"] is False


def test_manager_permissions() -> None:
    """Tests specific permission mappings configured for the MANAGER role."""
    assert ROLE_PERMISSIONS["MANAGER"]["can_mail"] == ["EMPLOYEE", "MANAGER", "CEO"]
    assert ROLE_PERMISSIONS["MANAGER"]["can_forward"] is True


def test_ceo_permissions() -> None:
    """Tests specific permission mappings configured for the CEO role."""
    assert ROLE_PERMISSIONS["CEO"]["can_mail"] == ["MANAGER"]
    assert ROLE_PERMISSIONS["CEO"]["can_forward"] is True


def test_employee_cannot_forward() -> None:
    """Tests the specific policy that employees are restricted from forwarding mails."""
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_forward"] is False


def test_ceo_cannot_mail_employee_directly() -> None:
    """Tests chain-of-command design enforcing that the CEO cannot mail employees directly.

    Documents current design: CEO can only mail MANAGER, not EMPLOYEE
    directly. If this is intentional (e.g., a chain-of-command policy),
    this test locks it in. If it's a gap, it'll need updating alongside
    the source.
    """
    assert "EMPLOYEE" not in ROLE_PERMISSIONS["CEO"]["can_mail"]