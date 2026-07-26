from core.crud.create import create_mail
from core.crud.read import inbox
from core.crud.read import sent_mails
from core.auth.logout import logout


def user_menu(session):

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
            sent_mails(user[0])

        elif choice == "4":
            logout(session)
            break

        else:
            print("Invalid Choice!")
