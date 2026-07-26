import psycopg


def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5431,
        dbname="Mail Automation System",
        user="postgres",
        password="20031382Ss@"
    )