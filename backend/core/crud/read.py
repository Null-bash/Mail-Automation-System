"""Read and display operations for the OCIMAIL application.

Handles retrieving, paginating, and viewing emails in the user's inbox
and sent folders. Also provides interactive menus for viewing specific
email details and triggering actions like reply, forward, or delete.
"""

from core.crud.create import forward_mail
from core.crud.delete import delete_mail
from core.crud.update import reply_to_mail
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
                m.subject,
                m.status,
                m.created_date
            FROM mails m
            JOIN users sender
                ON m.sender_id = sender.user_id
            WHERE
                m.receiver_id=%s
                AND m.receiver_deleted=FALSE
            ORDER BY m.created_date DESC
            LIMIT %s OFFSET %s;
        """, (user_id, PAGE_SIZE + 1, offset))

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

            print(f"{index}. {mail[2]}")
            print(f"   From   : {mail[1]}")
            print(f"   Status : {mail[3]}")
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

                selected_mail_id = mails[choice - 1][0]

                open_mail(
                    selected_mail_id,
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


def sent_mails(user_id, mail_id, page=0) -> None:
    """Displays the user's paginated sent emails and handles navigation.

    Fetches emails sent by the user that have not been soft-deleted by the sender, 
    ordered by creation date. Presents an interactive CLI menu to page through 
    the emails (Next/Previous) or select a specific email to view its details.

    Args:
        user_id (str or int): The unique database ID of the current user.
        mail_id (any): External parameter passed from the session/menu state.
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
                m.created_date
            FROM mails m
            JOIN users sender
                ON m.sender_id = sender.user_id
            JOIN users receiver
                ON m.receiver_id = receiver.user_id
            WHERE
                sender.user_id=%s
                AND m.sender_deleted=FALSE
            ORDER BY m.created_date DESC
            LIMIT %s OFFSET %s;
        """, (user_id, PAGE_SIZE + 1, offset))

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

            print(f"{index}. {mail[3]}")
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

                selected_mail_id = mails[choice - 1][0]

                via_mail(
                    selected_mail_id,
                    user_id
                )

        else:
            print("Invalid Choice!")

