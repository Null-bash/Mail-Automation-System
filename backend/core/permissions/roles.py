"""Role-based access control (RBAC) permissions for OCIMAIL.

Defines communication rules and action capabilities for each user role
within the system.
"""

ROLE_PERMISSIONS = {

    "EMPLOYEE": {
        "can_mail": ["MANAGER"],
        "can_forward": False
    },

    "MANAGER": {
        "can_mail": [
            "EMPLOYEE",
            "MANAGER",
            "CEO"
        ],
        "can_forward": True
    },

    "CEO": {
        "can_mail": ["MANAGER"],
        "can_forward": True
    },

    "ADMIN": {
        "can_mail": [],
        "can_forward": False
    }
}
"""dict[str, dict]: Dictionary mapping user roles to their allowed permissions.

Attributes:
    can_mail (list[str]): List of target roles the current role is allowed to message.
    can_forward (bool): Indicates whether the role has permission to forward emails.

Note:
    ADMIN is included here so that ROLE_PERMISSIONS.keys() remains the single
    source of truth for "what roles exist" (used by core.admin.create to
    validate the role given when creating a new user). Admins don't send or
    forward mail themselves, hence the empty/False permissions.
"""