from core.auth.login import login
from core.menus.user_menu import user_menu

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
            mail_id = {
                """
                SELECT mail_id FROM mails"""
            }

            print()
            print("Successfully Logged In!")
            print()

            user_menu(session, mail_id)

    elif choice == "2":

        print("Goodbye!")
        break

    else:

        print("Invalid Choice!")