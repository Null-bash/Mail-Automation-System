
"""User menu module for the OCIMAIL application.

Handles interactive navigation options for authenticated users, including
mail creation, viewing inbox or sent messages, and session termination.
"""

from core.auth.logout import logout
from core.crud.create import create_mail
from core.crud.read import inbox, sent_mails


def user_menu(session: dict, mail_id: set) -> None:
    """Displays and manages the interactive CLI menu for logged-in users.

    Continuously prompts the user for menu choices (create mail, check inbox,
    view sent mails, or logout) and delegates execution to the corresponding
    CRUD or authentication functions based on the user's role and inputs.

    Args:
        session (dict): Active user session dictionary containing user details
            under the "user" key.
        mail_id (set): SQL query or set of mail IDs passed downstream for mail actions.
    """
    user = session["user"]
    while True:

        print(f"""
=================================
Welcome {user[1]}
Role: {user[4]}
=================================
""")

        print("1. Create Mail")
        print("2. Inbox")
        print("3. Sent Mails")
        print("4. Logout")

        choice = input("> ")

        if choice == "1":
            create_mail(
                user[0],
                user[4]
            )

        elif choice == "2":
            inbox(user[0], user[4])

        elif choice == "3":
            sent_mails(user[0], mail_id)

        elif choice == "4":
            logout(session)
            break

        else:
            print("Invalid Choice!")
