"""Email reply functionality for the OCIMAIL application.

Handles the creation of reply emails, including prompting for user input,
linking the reply to the original message, and updating the status of the
original email in the database.
"""

from core.db import get_connection


def reply_to_mail(mail_id, current_user_id) -> None:
    """Prompts the user for a reply body and sends a response to an email.

    Fetches the original email's sender and subject to automatically populate 
    the receiver and construct a "Re: " subject line. Inserts the new reply 
    into the database linked by the 'reply_to' field, and updates the original 
    email's status to 'REPLIED' with the current timestamp.

    Args:
        mail_id (str or int): The unique database ID of the original email 
            being replied to.
        current_user_id (str or int): The unique database ID of the user 
            sending the reply.
    """
    reply_body = input("\nReply:\n").strip()

    if reply_body == "":
        print("\nReply cannot be empty!\n")
        return

    conn = get_connection()
    cur = conn.cursor()

    # Get original mail information
    cur.execute(
        """
        SELECT
            sender_id,
            subject
        FROM mails
        WHERE mail_id = %s;
        """,
        (mail_id,)
    )

    original_mail = cur.fetchone()

    if not original_mail:

        cur.close()
        conn.close()

        print("\nMail not found!\n")
        return

    receiver_id = original_mail[0]
    original_subject = original_mail[1]

    # Create the reply
    cur.execute(
        """
        INSERT INTO mails(
            sender_id,
            receiver_id,
            subject,
            body,
            reply_to
        )
        VALUES(
            %s,
            %s,
            %s,
            %s,
            %s
        );
        """,
        (
            current_user_id,
            receiver_id,
            f"Re: {original_subject}",
            reply_body,
            mail_id
        )
    )

    # Update original mail
    cur.execute(
        """
        UPDATE mails
        SET
            status='REPLIED',
            reacted_date=CURRENT_TIMESTAMP
        WHERE mail_id=%s;
        """,
        (mail_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nReply Sent Successfully!\n")