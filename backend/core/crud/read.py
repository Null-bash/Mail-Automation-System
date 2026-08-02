"""Read and display operations for the OCIMAIL application.

Handles retrieving, paginating, and viewing emails in the user's inbox
and sent folders. Also provides interactive menus for viewing specific
email details and triggering actions like reply, forward, or delete.
"""

from core.crud.create import forward_mail
from core.crud.delete import delete_mail, delete_forward
from core.crud.update import reply_to_mail, reply_to_forward
from core.db import get_connection


def inbox(user_id, role, page=0) -> None:
    """Displays the user's paginated inbox and handles navigation.

    Fetches received emails that have not been soft-deleted by the receiver, 
    ordered by creation date. Presents an interactive CLI menu to page through 
    emails (Next/Previous) or select a specific email to open.

    Args:
        user_id (str or int): The unique database ID of the current user.
        role (str): The role of the user (e.g., 'EMPLOYEE', 'MANAGER'), passed 
            down to determine available actions when opening an email.
        page (int, optional): The current page index for pagination. Defaults to 0.
    """
    PAGE_SIZE = 10

    while True:

        offset = page * PAGE_SIZE

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                m.mail_id,
                sender.email,
                NULL::text,
                m.subject,
                m.status::text,
                m.created_date,
                'MAIL'
            FROM mails m
            JOIN users sender
                ON m.sender_id = sender.user_id
            WHERE
                m.receiver_id=%s
                AND m.receiver_deleted=FALSE

            UNION ALL

            SELECT
                f.forward_id,
                creator.email,
                forwarder.email,
                m.subject,
                f.status::text,
                f.created_date,
                'FORWARD'
            FROM forwards f
            JOIN mails m
                ON m.mail_id=f.mail_id
            JOIN users creator
                ON creator.user_id=m.sender_id
            JOIN users forwarder
                ON forwarder.user_id=f.sender_id
            WHERE
                f.receiver_id=%s
                AND f.receiver_deleted=FALSE

            ORDER BY created_date DESC
            LIMIT %s OFFSET %s;
        """, (
            user_id,
            user_id,
            PAGE_SIZE + 1,
            offset
        ))

        rows = cur.fetchall()

        has_next = len(rows) > PAGE_SIZE

        mails = rows[:PAGE_SIZE]

        cur.close()
        conn.close()

        if not mails:
            print("\nYour inbox is empty.\n")
            return

        print("\n========== INBOX ==========\n")

        for index, mail in enumerate(mails, start=1):

            print(f"{index}. {mail[3]}")

            print(
                f"Type   : {mail[6]}"
            )

            print(
                f"From   : {mail[1]}"
            )

            if mail[6] == "FORWARD":
                print(
                    f"FORWARDED BY : {mail[2]}"
                )

            print(
                f"Status : {mail[4]}"
            )

            print(
                f"Date   : {mail[5].strftime('%d %b %Y | %H:%M')}"
            )
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
            continue

        elif choice == "P" and page > 0:
            page -= 1
            continue

        elif choice.isdigit():

            choice = int(choice)

            if 1 <= choice <= len(mails):

                selected_id = mails[choice - 1][0]

                mail_type = mails[choice - 1][6]

                if mail_type == "MAIL":

                    open_mail(
                        selected_id,
                        role,
                        user_id
                    )

                else:

                    open_forward(
                        selected_id,
                        role,
                        user_id
                    )

        else:
            print("Invalid Choice!")



def via_mail(mail_id, current_user_id) -> None:
    """Displays the details of a sent email and its action menu.

    Fetches and prints the full content (sender, receiver, subject, body, status, date) 
    of a specific sent email. Provides a nested CLI menu allowing the user to either 
    delete the email or go back.

    Args:
        mail_id (str or int): The unique database ID of the email to view.
        current_user_id (str or int): The unique database ID of the current user, 
            used for authorization if they choose to delete the email.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sender.email,
            receiver.email,
            m.subject,
            m.body,
            m.status,
            m.created_date
        FROM mails m
        JOIN users sender
            ON sender.user_id = m.sender_id
        JOIN users receiver
            ON receiver.user_id = m.receiver_id
        WHERE m.mail_id = %s;
    """, (mail_id,))

    mail = cur.fetchone()


    cur.close()
    conn.close()

    print("\n=========================")

    print("FROM:")
    print(mail[0])

    print("\nTO:")
    print(mail[1])

    print("\nSUBJECT:")
    print(mail[2])

    print("\nBODY:")
    print(mail[3])

    print("\nSTATUS:")
    print(mail[4])

    print("\nDATE:")
    print(mail[5].strftime("%d %b %Y | %H:%M"))

    print("\n=========================\n")

    while True:

            print("1. Delete")
            print("0. Back")

            choice = input("> ")


            if choice == "1":

                delete_mail(
                    mail_id,
                    current_user_id
                )
                return

            elif choice == "0":
                return

            else:
                print("\nInvalid Choice!\n")




def open_mail(mail_id, role, current_user_id) -> None:
    """Opens an inbox email, updates its status to SEEN, and shows actions.

    Fetches the full details of an email. If the email status is currently 'UNSEEN', 
    it updates the status to 'SEEN' and records the reaction time in the database. 
    Prints the email content and presents an action menu (Reply, Forward, Delete) 
    that dynamically adjusts based on the user's role.

    Args:
        mail_id (str or int): The unique database ID of the email to open.
        role (str): The role of the user (e.g., 'EMPLOYEE', 'MANAGER') which 
            determines if they have access to the Forward action.
        current_user_id (str or int): The unique database ID of the current user.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sender.email,
            receiver.email,
            m.subject,
            m.body,
            m.status,
            m.created_date
        FROM mails m
        JOIN users sender
            ON sender.user_id = m.sender_id
        JOIN users receiver
            ON receiver.user_id = m.receiver_id
        WHERE m.mail_id = %s;
    """, (mail_id,))

    mail = cur.fetchone()

    if mail[4] == "UNSEEN":

        cur.execute(
            """
            UPDATE mails
            SET
                status='SEEN',
                reacted_date=CURRENT_TIMESTAMP
            WHERE mail_id=%s;
            """,
            (mail_id,)
        )

        conn.commit()

        mail = (
            mail[0],
            mail[1],
            mail[2],
            mail[3],
            "SEEN",
            mail[5]
        )

    cur.close()
    conn.close()

    print("\n=========================")

    print("FROM:")
    print(mail[0])

    print("\nTO:")
    print(mail[1])

    print("\nSUBJECT:")
    print(mail[2])

    print("\nBODY:")
    print(mail[3])

    print("\nSTATUS:")
    print(mail[4])

    print("\nDATE:")
    print(mail[5].strftime("%d %b %Y | %H:%M"))

    print("\n=========================\n")

    while True:

        if role == "EMPLOYEE":

            print("1. Reply")
            print("2. Delete")
            print("0. Back")

            choice = input("> ")

            if choice == "1":

                reply_to_mail(
                    mail_id,
                    current_user_id
                )
                return

            elif choice == "2":

                delete_mail(
                    mail_id,
                    current_user_id
                )
                return

            elif choice == "0":
                return

            else:
                print("\nInvalid Choice!\n")

        else:

            print("1. Reply")
            print("2. Forward")
            print("3. Delete")
            print("0. Back")

            choice = input("> ")

            if choice == "1":

                reply_to_mail(
                    mail_id,
                    current_user_id
                )

                return

            elif choice == "2":

                forward_mail(
                    mail_id,
                    current_user_id,
                    role
                )

                return

            elif choice == "3":

                delete_mail(
                    mail_id,
                    current_user_id
                )

                return

            elif choice == "0":
                return

            else:
                print("\nInvalid Choice!\n")


def open_forward(
    forward_id,
    role,
    current_user_id
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            creator.email,
            receiver.email,
            m.subject,
            m.body,
            forwarder.email,
            forwarder.role,
            f.forward_note,
            f.status,
            f.created_date,
            m.mail_id
        FROM forwards f
        JOIN mails m
            ON m.mail_id=f.mail_id
        JOIN users creator
            ON creator.user_id=m.sender_id
        JOIN users receiver
            ON receiver.user_id=f.receiver_id
        JOIN users forwarder
            ON forwarder.user_id=f.sender_id
        WHERE f.forward_id=%s;
    """, (forward_id,))

    forward = cur.fetchone()

    original_mail_id = forward[9]

    if forward[7] == "UNSEEN":

        cur.execute("""
            UPDATE forwards
            SET
                status='SEEN',
                reacted_date=CURRENT_TIMESTAMP
            WHERE forward_id=%s;
        """, (forward_id,))

        conn.commit()

    cur.close()
    conn.close()

    print("\n=========================")

    print("FROM:")
    print(forward[0])

    print("\nTO:")
    print(forward[1])

    print("\nSUBJECT:")
    print(forward[2])

    print("\nBODY:")
    print(forward[3])

    print(f"\nFORWARD NOTE BY {forward[4]} / {forward[5]}:")
    print(forward[6])

    print("\nSTATUS:")

    if forward[7] == "UNSEEN":
        print("SEEN")
    else:
        print(forward[7])

    print("\nDATE:")
    print(
        forward[8].strftime(
            "%d %b %Y | %H:%M"
        )
    )

    print("\n=========================\n")

    while True:

        if role == "EMPLOYEE":

            print("1. Reply")
            print("2. Delete")
            print("0. Back")

            choice = input("> ")

            if choice == "1":

                reply_to_forward(
                    forward_id,
                    current_user_id
                )
                return

            elif choice == "2":

                delete_forward(
                    forward_id,
                    current_user_id
                )
                return

            elif choice == "0":
                return

            else:
                print("\nInvalid Choice!\n")

        else:

            print("1. Reply")
            print("2. Forward")
            print("3. Delete")
            print("0. Back")

            choice = input("> ")

            if choice == "1":

                reply_to_forward(
                    forward_id,
                    current_user_id
                )
                return

            elif choice == "2":

                forward_mail(
                    original_mail_id,
                    current_user_id,
                    role
                )
                return

            elif choice == "3":

                delete_forward(
                    forward_id,
                    current_user_id
                )
                return

            elif choice == "0":
                return

            else:
                print("\nInvalid Choice!\n")


def via_forward(forward_id, current_user_id) -> None:
    """Displays the details of a sent forward and its action menu.

    Fetches and prints the full content of a forward the current user sent:
    FROM is always the original creator of the mail (not the forwarder),
    TO is the forward's receiver, and a "FORWARD NOTE BY {email} / {role}"
    line identifies who forwarded it and in what capacity. Provides a menu
    allowing the user to delete the forward (marking their side as deleted)
    or go back.

    Args:
        forward_id (str or int): The unique database ID of the forward to view.
        current_user_id (str or int): The unique database ID of the current
            user, used for authorization if they choose to delete it.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            creator.email,
            receiver.email,
            m.subject,
            m.body,
            forwarder.email,
            forwarder.role,
            f.forward_note,
            f.status,
            f.created_date
        FROM forwards f
        JOIN mails m
            ON m.mail_id = f.mail_id
        JOIN users creator
            ON creator.user_id = m.sender_id
        JOIN users receiver
            ON receiver.user_id = f.receiver_id
        JOIN users forwarder
            ON forwarder.user_id = f.sender_id
        WHERE f.forward_id = %s;
    """, (forward_id,))

    forward = cur.fetchone()

    cur.close()
    conn.close()

    print("\n=========================")

    print("FROM:")
    print(forward[0])

    print("\nTO:")
    print(forward[1])

    print("\nSUBJECT:")
    print(forward[2])

    print("\nBODY:")
    print(forward[3])

    print(f"\nFORWARD NOTE BY {forward[4]} / {forward[5]}:")
    print(forward[6])

    print("\nSTATUS:")
    print(forward[7])

    print("\nDATE:")
    print(forward[8].strftime("%d %b %Y | %H:%M"))

    print("\n=========================\n")

    while True:

        print("1. Delete")
        print("0. Back")

        choice = input("> ")

        if choice == "1":

            delete_forward(
                forward_id,
                current_user_id
            )
            return

        elif choice == "0":
            return

        else:
            print("\nInvalid Choice!\n")


def sent_mails(user_id, mail_id, page=0) -> None:
    """Displays the user's paginated sent emails and handles navigation.

    Fetches emails sent by the user that have not been soft-deleted by the sender, 
    ordered by creation date. Presents an interactive CLI menu to page through 
    the emails (Next/Previous) or select a specific email to view its details.

    Args:
        user_id (str or int): The unique database ID of the current user.
        mail_id (any): Currently unused. Kept for call-site compatibility;
            consider removing if no caller relies on this positional slot.
        page (int, optional): The current page index for pagination. Defaults to 0.
    """
    PAGE_SIZE = 10

    while True:

        offset = page * PAGE_SIZE

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                m.mail_id,
                receiver.email,
                receiver.role,
                m.subject,
                m.created_date,
                'MAIL'
            FROM mails m
            JOIN users sender
                ON m.sender_id = sender.user_id
            JOIN users receiver
                ON m.receiver_id = receiver.user_id
            WHERE
                sender.user_id=%s
                AND m.sender_deleted=FALSE

            UNION ALL

            SELECT
                f.forward_id,
                receiver.email,
                receiver.role,
                om.subject,
                f.created_date,
                'FORWARD'
            FROM forwards f
            JOIN mails om
                ON om.mail_id = f.mail_id
            JOIN users sender
                ON f.sender_id = sender.user_id
            JOIN users receiver
                ON f.receiver_id = receiver.user_id
            WHERE
                sender.user_id=%s
                AND f.sender_deleted=FALSE

            ORDER BY created_date DESC
            LIMIT %s OFFSET %s;
        """, (user_id, user_id, PAGE_SIZE + 1, offset))

        rows = cur.fetchall()

        has_next = len(rows) > PAGE_SIZE

        mails = rows[:PAGE_SIZE]

        cur.close()
        conn.close()

        if not mails:
            print("\nYou haven't sent any mails yet.\n")
            return

        print("\n========== SENT MAILS ==========\n")

        for index, mail in enumerate(mails, start=1):

            subject = mail[3]

            if mail[5] == "FORWARD":
                subject = f"FWD: {subject}"

            print(f"{index}. {subject}")
            print(f"   Type   : {mail[5]}")
            print(f"   To     : {mail[1]}")
            print(f"   Role   : {mail[2]}")
            print(
                f"   Date   : "
                f"{mail[4].strftime('%d %b %Y | %H:%M')}"
            )
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
            continue

        elif choice == "P" and page > 0:
            page -= 1
            continue

        elif choice.isdigit():
        
            choice = int(choice)

            if 1 <= choice <= len(mails):

                selected_id = mails[choice - 1][0]

                item_type = mails[choice - 1][5]

                if item_type == "MAIL":

                    via_mail(
                        selected_id,
                        user_id
                    )

                else:

                    via_forward(
                        selected_id,
                        user_id
                    )

        else:
            print("Invalid Choice!")
