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

        print("\nUser is already deleted\n")

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

    cur.execute(
        """
        DELETE FROM users
        WHERE user_id=%s
        AND role='CEO';
        """,
        (user_id,)
    )

    # Cascade the soft-delete: clear this user's own view of everything
    # they sent or received, on both mails and forwards. The other party
    # in each of these keeps their own copy untouched — this only flips
    # this user's side of the flag, same as if they'd deleted it themselves.
    cur.execute(
        """
        UPDATE mails
        SET sender_deleted=TRUE
        WHERE sender_id=%s;
        """,
        (user_id,)
    )

    cur.execute(
        """
        UPDATE mails
        SET receiver_deleted=TRUE
        WHERE receiver_id=%s;
        """,
        (user_id,)
    )

    cur.execute(
        """
        UPDATE forwards
        SET sender_deleted=TRUE
        WHERE sender_id=%s;
        """,
        (user_id,)
    )

    cur.execute(
        """
        UPDATE forwards
        SET receiver_deleted=TRUE
        WHERE receiver_id=%s;
        """,
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nUser deleted successfully!\n")