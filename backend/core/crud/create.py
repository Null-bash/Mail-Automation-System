"""Email creation and forwarding functionalities for OCIMAIL.

Handles the interactive creation of new emails and the forwarding of existing
emails, including user input validation, role-based permission checks, and 
database operations.
"""

from core.db import get_connection
from core.permissions.roles import ROLE_PERMISSIONS


def create_mail(sender_id, sender_role) -> None:
    """Prompts the user to create and send a new email.

    Handles interactive CLI input for receiver email, subject, and body. 
    Validates the receiver's existence, ensures the sender is not emailing 
    themselves, and verifies role-based permissions before inserting the 
    new mail record into the database.

    Args:
        sender_id (str or int): The unique database ID of the user sending the mail.
        sender_role (str): The role of the sender (e.g., 'MANAGER', 'EMPLOYEE') 
            used to authorize the action.
    """
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
        WHERE email=%s
        AND is_active=TRUE;
        """,
        (receiver_email.lower().strip(),)
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



def forward_mail(mail_id, sender_id, sender_role) -> None:
    """Forwards an existing email to a new receiver.

    Verifies that the sender has forwarding privileges. Prompts for the receiver's
    email and an optional forward note. Applies business rules to ensure the
    email is not forwarded to the original sender or the current sender, and checks
    role permissions. Inserts a new mail record and logs the forward action.

    Args:
        mail_id (str or int): The unique database ID of the original mail to be forwarded.
        sender_id (str or int): The unique database ID of the user forwarding the mail.
        sender_role (str): The role of the user forwarding the mail, used for
            permission and rule validation.
    """
    if not ROLE_PERMISSIONS[sender_role]["can_forward"]:

        print(
            "\nYou don't have permission "
            "to forward mails!"
        )
        return

    receiver_email = input("\nReceiver Email: ").strip()

    if receiver_email == "":
        print("\nReceiver Email cannot be empty!")
        return

    forward_notes = input("Forward Note: ")

    conn = get_connection()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT user_id, role
        FROM users
        WHERE email=%s
        AND is_active=TRUE;
        """,
        (receiver_email.lower().strip(),)
    )

    receiver = cur.fetchone()

    if not receiver:

        print("\nReceiver does not exist!")

        cur.close()
        conn.close()
        return

    receiver_id = receiver[0]
    receiver_role = receiver[1]

    # -----------------------------
    # Get original sender
    # -----------------------------
    cur.execute(
        """
        SELECT sender_id
        FROM mails
        WHERE mail_id=%s;
        """,
        (mail_id,)
    )

    original_sender_id = cur.fetchone()[0]

    # Rule 1
    if receiver_id == original_sender_id:

        print(
            "\nYou cannot forward a mail "
            "back to its original sender!"
        )

        cur.close()
        conn.close()
        return

    # Rule 2
    if receiver_id == sender_id:

        print(
            "\nYou cannot forward a mail "
            "to yourself!"
        )

        cur.close()
        conn.close()
        return

    # Rule 3
    if receiver_role not in ROLE_PERMISSIONS[sender_role]["can_mail"]:

        print(
            "\nYou don't have permission "
            "to forward to this role!"
        )

        cur.close()
        conn.close()
        return

    forward_note = forward_notes

    # -----------------------------
    # Save the forward
    #
    # No new row is created in `mails` — the forward references the
    # ORIGINAL mail_id. This is what makes it show up automatically in
    # the receiver's inbox (via the UNION in inbox()) and lets us show
    # it in the sender's Sent Mails too, without duplicating content.
    # -----------------------------
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

    print("\nMail forwarded successfully!")