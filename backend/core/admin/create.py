"""User creation functionality for OCIMAIL administrators.

Allows an admin to create new user accounts, enforcing email uniqueness
and validating that each user is assigned exactly one recognized role.
"""

import bcrypt

from core.db import get_connection
from core.permissions.roles import ROLE_PERMISSIONS


def create_user(admin_id, name, email, password, role) -> None:
    """Creates a new user account.

    Validates that the role is one of the roles defined in ROLE_PERMISSIONS
    (a user can only ever have exactly one role, since `role` is a single
    column), and that no existing user already has the given email, before
    inserting the new user record with a hashed password.

    Args:
        admin_id (str or int): The unique database ID of the admin performing
            the creation. Not used in the query itself, but kept so this
            action can be logged/audited later if needed.
        name (str): The display name for the new user.
        email (str): The email address for the new user. Must be unique.
        password (str): The plaintext password for the new user; hashed
            before storage.
        role (str): The role to assign to the new user. Must be one of the
            keys in ROLE_PERMISSIONS (EMPLOYEE, MANAGER, CEO, ADMIN).
    """
    name = name.strip()
    email = email.strip()
    role = role.strip().upper()

    if name == "":
        print("\nName cannot be empty!\n")
        return

    if email == "":
        print("\nEmail cannot be empty!\n")
        return

    if password == "":
        print("\nPassword cannot be empty!\n")
        return

    if role not in ROLE_PERMISSIONS:

        print(
            f"\nInvalid role! Must be one of: "
            f"{', '.join(ROLE_PERMISSIONS.keys())}\n"
        )
        return

    conn = get_connection()
    cur = conn.cursor()

    # Enforce the single-CEO rule: refuse to create another CEO if one
    # already exists in the system, whether active or deactivated.
    if role == "CEO":

        cur.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='CEO';
            """
        )

        ceo_count = cur.fetchone()[0]

        if ceo_count > 0:

            print(
                "\nA CEO already exists! Only one CEO "
                "is allowed in the system.\n"
            )

            cur.close()
            conn.close()
            return

    # Enforce uniqueness: refuse to create a user that already exists
    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE email=%s;
        """,
        (email,)
    )

    existing = cur.fetchone()

    if existing:

        print("\nA user with this email already exists!\n")

        cur.close()
        conn.close()
        return

    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    cur.execute(
        """
        INSERT INTO users(
            name,
            email,
            password_hash,
            role,
            is_active
        )
        VALUES(
            %s,
            %s,
            %s,
            %s,
            TRUE
        );
        """,
        (
            name,
            email,
            hashed_password,
            role
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    print(f"\nUser '{email}' created successfully as {role}!\n")