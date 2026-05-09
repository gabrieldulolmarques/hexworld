from pathlib import Path
from sqlite3 import Connection

SCHEMA_PATH = Path(__file__).resolve().parent / "scripts" / "schema.sql"

def create_schema(connection: Connection) -> None:
    try:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(sql)
        connection.commit()
    except Exception as exception:
        print(f"Error creating database schema: {exception}")
        raise
