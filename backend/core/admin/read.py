"""User listing functionality for OCIMAIL administrators.

Lets an admin browse all user accounts, including their role and whether
they're currently active or deactivated.
"""

from core.db import get_connection


def list_users(admin_id, page=0) -> None:
    """Displays a paginated list of all user accounts.

    Args:
        admin_id (str or int): The unique database ID of the admin viewing
            the list. Not used in the query itself, but kept so this action
            can be logged/audited later if needed.
        page (int, optional): The current page index for pagination. Defaults to 0.
    """
    PAGE_SIZE = 10

    while True:

        offset = page * PAGE_SIZE

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                user_id,
                name,
                email,
                role,
                is_active
            FROM users
            ORDER BY created_at
            LIMIT %s OFFSET %s;
            """,
            (PAGE_SIZE + 1, offset)
        )

        rows = cur.fetchall()

        has_next = len(rows) > PAGE_SIZE

        users = rows[:PAGE_SIZE]

        cur.close()
        conn.close()

        if not users:
            print("\nNo users found.\n")
            return

        print("\n========== USERS ==========\n")

        for index, user in enumerate(users, start=1):

            print(f"{index}. {user[1]} ({user[2]})")
            print(f"   ID     : {user[0]}")
            print(f"   Role   : {user[3]}")
            print(f"   Status : {'ACTIVE' if user[4] else 'DEACTIVATED'}")
            print()

        print("0. Back")

        if page > 0:
            print("P. Previous")

        if has_next:
            print("N. Next")

        choice = input("> ").strip().upper()

        if choice == "0":
            return

        elif choice == "N" and has_next:
            page += 1
            continue

        elif choice == "P" and page > 0:
            page -= 1
            continue

        else:
            print("Invalid Choice!")