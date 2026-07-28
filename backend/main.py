# main.py
from core.auth.login import login
from core.menus.user_menu import user_menu
from core.db import get_connection

MENU_TEXT = """
=================================
            OCIMAIL
=================================

1. Login
2. Exit
"""

def get_mail_ids():
    get_connection()
    return []

def run_menu_once(choice, login_fn=login, menu_fn=user_menu):
    """Handles a single choice. Returns False if the app should exit."""
    if choice == "1":
        user = login_fn()
        if user:
            session = {"user": user}
            mail_ids = get_mail_ids()
            print("\nSuccessfully Logged In!\n")
            menu_fn(session, mail_ids)
        return True

    elif choice == "2":
        print("Goodbye!")
        return False

    else:
        print("Invalid Choice!")
        return True

def main():
    while True:
        print(MENU_TEXT)
        choice = input("> ")
        if not run_menu_once(choice):
            break

if __name__ == "__main__":
    main()