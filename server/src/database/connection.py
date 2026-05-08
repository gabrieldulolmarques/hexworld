import sqlite3
import threading
import os
from pathlib import Path

_local = threading.local()
    
def get_database_path() -> Path:
    configured = os.getenv("DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "hexworld.db"

def get_connection() -> sqlite3.Connection:
    if not hasattr(_local, "connection") or _local.connection is None:
        try:
            db_path = get_database_path()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            _local.connection = sqlite3.connect(db_path)
            _local.connection.row_factory = sqlite3.Row
        except sqlite3.Error as exception:
            print(f"Error getting database connection: {exception}")
        except Exception as exception:
            print(f"Unexpected error getting database connection: {exception}")
    return _local.connection

def close_connection() -> None:
    if hasattr(_local, "connection") and _local.connection is not None:
        try:
            _local.connection.close()
        except sqlite3.Error as exception:
            print(f"Error closing database connection: {exception}")
        except Exception as exception:
            print(f"Unexpected error closing database connection: {exception}")
        finally:
            _local.connection = None