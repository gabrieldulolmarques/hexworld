import logging
from pathlib import Path
from sqlite3 import Connection

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent / "scripts" / "schema.sql"

def create_schema(connection: Connection) -> None:
    try:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(sql)
    except Exception:
        connection.rollback()
        logger.exception("Error creating database schema")
        raise
