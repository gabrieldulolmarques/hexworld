from os import getenv
from pathlib import Path
from sqlite3 import Connection, Row, connect
from threading import local

_local = local()

def get_database_path() -> Path:
    configured = getenv("DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "hexworld.db"

def get_connection() -> Connection:
    if not hasattr(_local, "connection") or _local.connection is None:
        try:
            db_path = get_database_path()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            _local.connection = connect(db_path)
            _local.connection.row_factory = Row
        except Exception as exception:
            print(f"Error getting database connection: {exception}")
            raise
    return _local.connection

def close_connection() -> None:
    if hasattr(_local, "connection") and _local.connection is not None:
        try:
            _local.connection.close()
        except Exception as exception:
            print(f"Error closing database connection: {exception}")
        finally:
            _local.connection = None
