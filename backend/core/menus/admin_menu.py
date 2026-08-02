"""Interactive menu for admin users of the OCIMAIL application.

Presents the available admin actions (create user, list users, delete user)
and dispatches to the appropriate handler based on the admin's selection.
"""

from core.admin.create import create_user
from core.admin.read import list_users
from core.admin.delete import delete_user


def admin_menu(session) -> None:
    """Displays the admin's main menu and handles navigation.

    Args:
        session: The current admin's session data. Index 0 is expected to
            be the admin's user_id (mirroring how user_menu.py reads
            session[0] as user_id and session[4] as role).
    """

    admin_id = session["user"][0]

    while True:

        print("\n========== ADMIN MENU ==========\n")
        print("1. Create User")
        print("2. List Users")
        print("3. Delete User")
        print("0. Logout")

        choice = input("> ").strip()

        if choice == "1":

            name = input("New user's name: ").strip()
            email = input("New user's email: ").strip()
            password = input("New user's password: ").strip()
            role = input("Role (EMPLOYEE/MANAGER/CEO): ").strip().upper()

            create_user(
                admin_id,
                name,
                email,
                password,
                role
            )

        elif choice == "2":

            list_users(admin_id)

        elif choice == "3":

            user_id_input = input("User ID to deactivate: ").strip()

            if user_id_input == "":
                print("\nInvalid User ID!\n")
                continue

            delete_user(
                admin_id,
                user_id_input
            )

        elif choice == "0":
            return

        else:
            print("\nInvalid Choice!\n")