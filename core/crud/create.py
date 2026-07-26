from core.db import get_connection
from core.permissions.roles import ROLE_PERMISSIONS


def create_mail(sender_id, sender_role):

    receiver_email = input("Receiver Email: ")
    subject = input("Subject: ")
    body = input("Body: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE email=%s;
        """,
        (receiver_email,)
    )

    receiver = cur.fetchone()

    receiver_id = receiver[0]
    receiver_role = receiver[1]

    if receiver_role not in ROLE_PERMISSIONS[
        sender_role
    ]["can_mail"]:

        print(
            "\nYou don't have permission "
            "to send mail to this role!\n"
        )

        cur.close()
        conn.close()
        return

    if not receiver:

        print("\nReceiver does not exist!")

        cur.close()
        conn.close()
        return

    receiver_id = receiver[0]

    cur.execute(
        """
        INSERT INTO mails(
            sender_id,
            receiver_id,
            subject,
            body
        )
        VALUES(
            %s,
            %s,
            %s,
            %s
        );
        """,
        (
            sender_id,
            receiver_id,
            subject,
            body
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nMail Sent Successfully!")


def forward_mail(mail_id,sender_id,sender_role):

    if not ROLE_PERMISSIONS[sender_role]["can_forward"]:

        print(
            "\nYou don't have permission "
            "to forward mails!"
        )

        return
    receiver_email = input("\nReceiver Email: ")
    forward_note = input("Forward Note: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE email=%s;
        """,
        (receiver_email,)
    )

    receiver = cur.fetchone()

    if not receiver:

        print("\nReceiver does not exist!")

        cur.close()
        conn.close()
        return

    receiver_id = receiver[0]

    cur.execute(
        """
        INSERT INTO forwards(
            sender_id,
            receiver_id,
            forward_note,
            mail_id
        )
        VALUES(
            %s,
            %s,
            %s,
            %s
        );
        """,
        (
            sender_id,
            receiver_id,
            forward_note,
            mail_id
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nMail Forwarded Successfully!\n")