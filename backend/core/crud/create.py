from core.db import get_connection
from core.permissions.roles import ROLE_PERMISSIONS


def create_mail(sender_id, sender_role):

    receiver_email = input(
        "Receiver Email: "
    ).strip()

    if receiver_email == "":

        print(
            "\nReceiver Email cannot be empty!"
        )

        return
    
    subject = input("Subject: ").strip()

    if subject == "":

        print(
            "\nSubject cannot be empty!"
        )

        return


    body = input("Body: ").strip()

    if body == "":

        print(
            "\nBody cannot be empty!"
        )

        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            user_id,
            role
        FROM users
        WHERE email=%s;
        """,
        (receiver_email,)
    )

    receiver = cur.fetchone()
    if not receiver:

        print(
            "\nReceiver does not exist!"
        )

        cur.close()
        conn.close()
        return


    receiver_id = receiver[0]
    receiver_role = receiver[1]

    if sender_id == receiver_id:

        print(
            "\nYou cannot send a mail to yourself!"
        )

        cur.close()
        conn.close()
        return

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


def forward_mail(mail_id, sender_id, sender_role):

    if not ROLE_PERMISSIONS[sender_role]["can_forward"]:

        print(
            "\nYou don't have permission "
            "to forward mails!"
        )

        return

    receiver_email = input(
        "\nReceiver Email: "
    )

    if receiver_email == "":

        print(
            "\nReceiver Email cannot be empty!"
        )

        return

    forward_note = input(
        "Forward Note: "
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            user_id,
            role
        FROM users
        WHERE email=%s;
        """,
        (receiver_email,)
    )

    receiver = cur.fetchone()

    if not receiver:

        print(
            "\nReceiver does not exist!"
        )

        cur.close()
        conn.close()
        return

    receiver_id = receiver[0]
    receiver_role = receiver[1]

    cur.execute(
        """
        SELECT sender_id
        FROM mails
        WHERE mail_id=%s;
        """,
        (mail_id,)
    )

    original_sender_id = cur.fetchone()[0]

    if receiver_id == original_sender_id:

        print(
            "\nYou cannot forward a mail "
            "back to its original sender!"
        )

        cur.close()
        conn.close()
        return

    # Rule 2
    if sender_id == receiver_id:

        print(
            "\nYou cannot forward mail to yourself!"
        )

        cur.close()
        conn.close()
        return

    # Rule 1
    if receiver_role not in ROLE_PERMISSIONS[
        sender_role
    ]["can_mail"]:

        print(
            "\nYou don't have permission "
            "to forward to this role!"
        )

        cur.close()
        conn.close()
        return

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

    print(
        "\nMail Forwarded Successfully!\n"
    )