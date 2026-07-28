# test/permissions/test_role.py
from core.permissions.roles import ROLE_PERMISSIONS


def test_all_expected_roles_present():
    assert set(ROLE_PERMISSIONS.keys()) == {"EMPLOYEE", "MANAGER", "CEO"}


def test_every_role_has_required_keys():
    for role, perms in ROLE_PERMISSIONS.items():
        assert "can_mail" in perms, f"{role} missing 'can_mail'"
        assert "can_forward" in perms, f"{role} missing 'can_forward'"


def test_can_mail_values_are_lists_of_valid_roles():
    valid_roles = set(ROLE_PERMISSIONS.keys())
    for role, perms in ROLE_PERMISSIONS.items():
        assert isinstance(perms["can_mail"], list), f"{role}'s can_mail should be a list"
        for target in perms["can_mail"]:
            assert target in valid_roles, f"{role} can_mail references unknown role '{target}'"


def test_can_forward_values_are_booleans():
    for role, perms in ROLE_PERMISSIONS.items():
        assert isinstance(perms["can_forward"], bool), f"{role}'s can_forward should be a bool"


def test_employee_permissions():
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_mail"] == ["MANAGER"]
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_forward"] is False


def test_manager_permissions():
    assert ROLE_PERMISSIONS["MANAGER"]["can_mail"] == ["EMPLOYEE", "MANAGER", "CEO"]
    assert ROLE_PERMISSIONS["MANAGER"]["can_forward"] is True


def test_ceo_permissions():
    assert ROLE_PERMISSIONS["CEO"]["can_mail"] == ["MANAGER"]
    assert ROLE_PERMISSIONS["CEO"]["can_forward"] is True


def test_employee_cannot_forward():
    assert ROLE_PERMISSIONS["EMPLOYEE"]["can_forward"] is False


def test_ceo_cannot_mail_employee_directly():
    """
    Documents current design: CEO can only mail MANAGER, not EMPLOYEE
    directly. If this is intentional (e.g. a chain-of-command policy),
    this test locks it in. If it's a gap, it'll need updating alongside
    the source.
    """
    assert "EMPLOYEE" not in ROLE_PERMISSIONS["CEO"]["can_mail"]