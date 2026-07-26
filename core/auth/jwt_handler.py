import jwt
from datetime import datetime, timedelta

SECRET_KEY = (
    "mail_automation_system_super_secret_key_2026"
)

ALGORITHM = "HS256"


def generate_token(user):

    payload = {
        "user_id": str(user[0]),
        "email": user[2],
        "role": user[4],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(token):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None