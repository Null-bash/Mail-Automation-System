import os
import psycopg


def get_connection():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", 5431),
        dbname=os.environ.get("DB_NAME", "Mail Automation System"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"],
    )