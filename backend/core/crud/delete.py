from core.db import get_connection


def delete_mail(mail_id, current_user_id):

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