from os import getenv
from pathlib import Path
from sqlite3 import Connection, Row, connect
from threading import local
from traceback import format_exc

_local = local()

def get_database_path() -> Path:
    configured = getenv("DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "hexworld.db"

def get_connection() -> Connection:
    connection = getattr(_local, "connection", None)
    if connection is None:
        try:
            database_path = get_database_path()
            database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = connect(database_path)
            connection.row_factory = Row
            connection.execute("PRAGMA foreign_keys = ON")
            _local.connection = connection
        except Exception as exception:
            print(f"Error getting database connection: {exception}")
            print(format_exc())
            raise
    return connection

def close_connection() -> None:
    connection = getattr(_local, "connection", None)
    if connection is not None:
        try:
            connection.close()
        except Exception as exception:
            print(f"Error closing database connection: {exception}")
            print(format_exc())
        finally:
            _local.connection = None
