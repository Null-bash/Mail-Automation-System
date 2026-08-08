"""Authentication module for the OCIMAIL application.

Handles user login by verifying provided credentials against the database 
records and returning the authenticated user data.
"""

import bcrypt

from core.db import get_connection


def login() -> tuple | None:
    """Prompts for user credentials and authenticates against the database.

    Requests an email and password from the user via standard input. Looks
    up the user by email, then verifies the given password against the
    bcrypt hash stored in 'password_hash' (rather than comparing plaintext
    against the hash in SQL, which can never match). Also checks that the
    account is active before allowing login.

    Returns:
        tuple or None: The user's full database record (same shape as
        before — SELECT * — so any existing code indexing into it, e.g.
        user[0] for user_id, keeps working exactly as it did) if
        authentication succeeds. Returns None if the email doesn't exist,
        the password is wrong, or the account is deactivated.
    """
    email = input("Email: ")
    password = input("Password: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE email=%s
        AND is_active=TRUE;
        """,
        (email.lower().strip(),)
    )

    user = cur.fetchone()

    if not user:

        cur.close()
        conn.close()

        print()
        print("Invalid Credentials!")

        return None

    # Look up columns by name rather than assuming a fixed position, so
    # this doesn't depend on guessing the table's exact column order.
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    stored_hash = user[columns.index("password_hash")]

    password_matches = bcrypt.checkpw(
        password.encode("utf-8"),
        stored_hash.encode("utf-8")
    )

    if not password_matches:

        print()
        print("Invalid Credentials!")

        return None

    is_active = user[columns.index("is_active")]

    if not is_active:

        print()
        print("This account has been deactivated.")

        return None

    print()
    print(f"Welcome {user[columns.index('name')]}!")

    return user