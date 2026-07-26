from core.auth.login import login
from core.auth.jwt_handler import generate_token
from core.menus.user_menu import user_menu

while True:

    print("""
=================================
     MAIL AUTOMATION SYSTEM
=================================

1. Login
2. Exit
""")

    choice = input("> ")

    if choice == "1":

        user = login()

        if user:

            token = generate_token(user)

            session = {
                "user": user,
                "token": token
            }

            print()
            print("Successfully Logged In!")
            print()

            user_menu(session)

    elif choice == "2":

        print("Goodbye!")
        break

    else:

        print("Invalid Choice!")