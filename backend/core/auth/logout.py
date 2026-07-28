
"""Session termination functionality for the OCIMAIL application.

Handles the user logout process by safely clearing the active session data.
"""

def logout(session: dict) -> None:
    """Logs the current user out by clearing the session data.

    Empties the provided session dictionary to remove user credentials 
    and state, effectively logging the user out of the application, 
    and prints a confirmation message.

    Args:
        session (dict): The active session dictionary containing user details.
    """
    session.clear()

    print(
        "\nSuccessfully Logged Out!\n"
    )