"""Authentication module for the OCIMAIL application.

Handles user login by verifying provided credentials against the database 
records and returning the authenticated user data.
"""

from core.db import get_connection


def login() -> tuple | None:
    """Prompts for user credentials and authenticates against the database.

    Requests an email and password from the user via standard input. Queries
    the database to find a matching user record based on the provided email 
    and password hash. 

    Returns:
        tuple or None: A tuple containing the user's database record (e.g., 
        ID, name, email, password_hash, role) if authentication is successful. 
        Returns None if the credentials are invalid.
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
        AND password_hash=%s;
        """,
        (email, password)
    )

    user = cur.fetchone()
    

    cur.close()
    conn.close()

    if user:
        print()
        print(f"Welcome {user[1]}!")
        return user

    print()
    print("Invalid Credentials!")

    return None