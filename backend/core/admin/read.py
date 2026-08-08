"""User listing functionality for OCIMAIL administrators.

Lets an admin browse all user accounts, including their role and whether
they're currently active or deactivated.
"""

from core.db import get_connection


def list_users(admin_id, page=0) -> None:
    """Display a paginated list of all user accounts.

    Args:
        admin_id (str or int):
            Unique ID of the admin viewing the users.
            Currently not used in the query, but kept for future
            logging/auditing functionality.

        page (int, optional):
            Current page index for pagination.
            Defaults to 0.
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
            ORDER BY created_at ASC, user_id ASC
            LIMIT %s OFFSET %s;
            """,
            (PAGE_SIZE + 1, offset)
        )

        rows = cur.fetchall()

        cur.close()
        conn.close()

        # We request one extra row to determine whether
        # another page exists.
        has_next = len(rows) > PAGE_SIZE

        # Only show the requested page.
        users = rows[:PAGE_SIZE]

        if not users:

            print("\nNo users found.\n")

            return

        print("\n========== USERS ==========\n")

        for index, user in enumerate(users, start=1):

            user_id = user[0]
            name = user[1]
            email = user[2]
            role = user[3]
            is_active = user[4]

            print(
                f"{index}. {name} ({email})"
            )

            print(f"   ID     : {user_id}")
            print(f"   Role   : {role}")

            status = "ACTIVE" if is_active else "DELETED"

            print(f"   Status : {status}")

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

        elif choice == "P" and page > 0:

            page -= 1

        else:

            print("\nInvalid Choice!\n")