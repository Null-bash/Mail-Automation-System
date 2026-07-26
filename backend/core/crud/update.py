from core.db import get_connection


def reply_to_mail(mail_id, current_user_id):

    reply_body = input("\nReply:\n")

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