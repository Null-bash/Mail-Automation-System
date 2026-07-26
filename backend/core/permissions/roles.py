
ROLE_PERMISSIONS = {

    "EMPLOYEE": {
        "can_mail": ["MANAGER"],
        "can_forward": False
    },

    "MANAGER": {
        "can_mail": [
            "EMPLOYEE",
            "CEO"
        ],
        "can_forward": True
    },

    "CEO": {
        "can_mail": ["MANAGER"],
        "can_forward": True
    }
}