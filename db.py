"""
db.py - Database Connection and Query Management for YatraSetu
Handles MySQL connections using official mysql-connector-python,
ensuring parameterized queries, transaction safety, and clean resource cleanup.
"""

import mysql.connector
from mysql.connector import Error as MySQLError
from contextlib import contextmanager
from config import Config

class DatabaseConnectionError(Exception):
    """Raised when connecting to MySQL server fails."""
    pass

class DatabaseQueryError(Exception):
    """Raised when an executed query fails or violates constraints."""
    pass


def get_db_connection(include_database=True):
    """
    Creates and returns a raw connection to the MySQL server.
    Raises DatabaseConnectionError if connection fails.
    """
    config = Config.get_db_config(include_database=include_database)
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except MySQLError as err:
        # Avoid leaking internal secrets or passwords in exception message
        error_msg = f"Unable to connect to MySQL at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}. Error code {err.errno}: {err.msg}"
        raise DatabaseConnectionError(error_msg) from None


def check_db_connection():
    """
    Tests connectivity to MySQL server and checks if the database exists.
    Returns (status: bool, message: str).
    """
    try:
        conn = get_db_connection(include_database=False)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]

        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE %s;", (Config.MYSQL_DATABASE,))
        db_exists = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        if db_exists:
            return True, f"Connected to MySQL {version}. Database '{Config.MYSQL_DATABASE}' is ready."
        else:
            return False, f"Connected to MySQL {version}, but database '{Config.MYSQL_DATABASE}' does not exist yet. Run init_db.py to create it."
    except DatabaseConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Connection check failed: {str(e)}"


@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager providing a MySQL cursor.
    Safely commits or rolls back transactions and guarantees closing cursor and connection.

    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO ...", (val,))
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection(include_database=True)
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
        if commit:
            conn.commit()
    except MySQLError as err:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        raise DatabaseQueryError(f"Database error ({err.errno}): {err.msg}") from err
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def fetch_all(query, params=None):
    """
    Executes a SELECT query and returns all matching rows as dictionaries.
    """
    with get_db_cursor(commit=False, dictionary=True) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def fetch_one(query, params=None):
    """
    Executes a SELECT query and returns the first matching row as a dictionary (or None).
    """
    with get_db_cursor(commit=False, dictionary=True) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute_query(query, params=None, commit=True):
    """
    Executes an INSERT, UPDATE, or DELETE query.
    Returns the lastrowid for INSERTs, or rowcount for UPDATE/DELETE.
    """
    with get_db_cursor(commit=commit, dictionary=True) as cursor:
        cursor.execute(query, params or ())
        if cursor.lastrowid:
            return cursor.lastrowid
        return cursor.rowcount
