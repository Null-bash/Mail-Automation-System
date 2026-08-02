"""Email deletion functionality for the OCIMAIL application.

Provides capabilities for users to soft-delete emails from their inbox
or sent folders by toggling visibility flags, ensuring the record remains
accessible for the other party.
"""

from core.db import get_connection


def delete_mail(mail_id, current_user_id) -> None:
    """Soft-deletes an email for the specified user.

    Fetches the mail record to determine if the requesting user is the sender
    or the receiver. Updates the database by setting either the 'sender_deleted'
    or 'receiver_deleted' flag to TRUE, effectively hiding the email from the
    user's view without permanently erasing the database row.

    Args:
        mail_id (str or int): The unique identifier of the mail to be deleted.
        current_user_id (str or int): The unique database ID of the user
            attempting to delete the mail.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            sender_id,
            receiver_id
        FROM mails
        WHERE mail_id=%s;
        """,
        (mail_id,)
    )

    mail = cur.fetchone()

    sender_id = mail[0]
    receiver_id = mail[1]

    # Sender deletes
    if current_user_id == sender_id:

        cur.execute(
            """
            UPDATE mails
            SET sender_deleted=TRUE
            WHERE mail_id=%s;
            """,
            (mail_id,)
        )

    # Receiver deletes
    elif current_user_id == receiver_id:

        cur.execute(
            """
            UPDATE mails
            SET receiver_deleted=TRUE
            WHERE mail_id=%s;
            """,
            (mail_id,)
        )

    conn.commit()

    cur.close()
    conn.close()

    print("\nMail Deleted Successfully!\n")


def delete_forward(forward_id, current_user_id) -> None:
    """Soft-deletes a forward for the specified user.

    Fetches the forward record to determine if the requesting user is the
    sender or the receiver of that specific forward. Updates the database by
    setting either the 'sender_deleted' or 'receiver_deleted' flag to TRUE,
    effectively hiding the forward from the user's view without permanently
    erasing the database row.

    Args:
        forward_id (str or int): The unique identifier of the forward to be deleted.
        current_user_id (str or int): The unique database ID of the user
            attempting to delete the forward.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            sender_id,
            receiver_id
        FROM forwards
        WHERE forward_id=%s;
        """,
        (forward_id,)
    )

    forward = cur.fetchone()

    sender_id = forward[0]
    receiver_id = forward[1]

    # Sender deletes
    if current_user_id == sender_id:

        cur.execute(
            """
            UPDATE forwards
            SET sender_deleted=TRUE
            WHERE forward_id=%s;
            """,
            (forward_id,)
        )

    # Receiver deletes
    elif current_user_id == receiver_id:

        cur.execute(
            """
            UPDATE forwards
            SET receiver_deleted=TRUE
            WHERE forward_id=%s;
            """,
            (forward_id,)
        )

    conn.commit()

    cur.close()
    conn.close()

    print("\nForward Deleted Successfully!\n")