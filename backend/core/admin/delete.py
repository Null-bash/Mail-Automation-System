"""User deactivation functionality for OCIMAIL administrators.

Soft-deletes user accounts by flagging them inactive rather than removing
the row outright, preserving mail/forward history for both the user and
anyone who exchanged mail with them.
"""

from core.db import get_connection


def delete_user(admin_id, user_id) -> None:
    """Deactivates a user account.

    Args:
        admin_id (str or int): The unique database ID of the admin performing
            the deletion. Not used in the query itself, but kept so this
            action can be logged/audited later if needed.
        user_id (str or int): The unique database ID of the user to deactivate.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT is_active
        FROM users
        WHERE user_id=%s;
        """,
        (user_id,)
    )

    user = cur.fetchone()

    if not user:

        print("\nUser not found!\n")

        cur.close()
        conn.close()
        return

    if not user[0]:

        print("\nUser is already deactivated!\n")

        cur.close()
        conn.close()
        return

    cur.execute(
        """
        UPDATE users
        SET is_active=FALSE
        WHERE user_id=%s;
        """,
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nUser deactivated successfully!\n")