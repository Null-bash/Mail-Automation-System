from core.db import get_connection


def login():

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