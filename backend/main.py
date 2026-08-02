"""Main entry point for the OCIMAIL application.

This script manages the primary CLI user menu, handling top-level navigation
for authentication (login) and application termination.
"""

from core.auth.login import login
from core.menus.user_menu import user_menu
from core.menus.admin_menu import admin_menu


def main() -> None:
    """Runs the interactive main menu loop for OCIMAIL.

    Prompts the user to log in or exit. Upon successful authentication,
    initializes the user session and delegates control to the user menu
    interface, or the admin menu if the account's role is ADMIN.
    """
    while True:
        print("""
=================================
            OCIMAIL
=================================

1. Login
2. Exit
""")

        choice = input("> ")

        if choice == "1":
            user = login()

            if user:
                session = {
                    "user": user,
                }

                print()
                print("Successfully Logged In!")
                print()

                if user[4] == "ADMIN":
                    admin_menu(session)
                else:
                    user_menu(session, None)

        elif choice == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid Choice!")


if __name__ == "__main__":
    main()