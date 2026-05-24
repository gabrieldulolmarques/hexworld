from pathlib import Path
from sqlite3 import Connection
from traceback import format_exc

from database.migrate import migrate_schema

SCHEMA_PATH = Path(__file__).resolve().parent / "scripts" / "schema.sql"

def create_schema(connection: Connection) -> None:
    try:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(sql)
        migrate_schema(connection)
        connection.commit()
    except Exception as exception:
        connection.rollback()
        print(f"Error creating database schema: {exception}")
        print(format_exc())
        raise
