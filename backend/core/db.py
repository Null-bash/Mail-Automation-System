"""Database connection management for the Mail Automation System.

Provides utility functions to establish connections with the PostgreSQL database
using configuration settings retrieved from environment variables.
"""

import os

import psycopg


def get_connection() -> psycopg.Connection:
    """Establishes and returns a connection to the PostgreSQL database.

    Reads database configuration options from environment variables, falling back
    to default values where appropriate.

    Returns:
        psycopg.Connection: An active PostgreSQL connection object.

    Raises:
        KeyError: If the required 'DB_PASSWORD' environment variable is missing.
        psycopg.OperationalError: If the connection attempt to the database fails.
    """
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", 5431),
        dbname=os.environ.get("DB_NAME", "Mail Automation System"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"],
    )