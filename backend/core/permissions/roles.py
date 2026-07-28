
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
    }
}
"""dict[str, dict]: Dictionary mapping user roles to their allowed permissions.

Attributes:
    can_mail (list[str]): List of target roles the current role is allowed to message.
    can_forward (bool): Indicates whether the role has permission to forward emails.
"""