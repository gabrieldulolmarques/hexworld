"""Add missing columns on existing SQLite databases (CREATE IF NOT EXISTS is not enough)."""
from sqlite3 import Connection, OperationalError

# (table, column, type, backfill from column or None)
_COLUMN_MIGRATIONS: list[tuple[str, str, str, str | None]] = [
    ("user", "updated_at", "TEXT", "created_at"),
    ("session", "updated_at", "TEXT", "created_at"),
    ("map", "updated_at", "TEXT", "created_at"),
    ("user_map", "updated_at", "TEXT", "created_at"),
    ("tile", "updated_at", "TEXT", "created_at"),
    ("structure", "updated_at", "TEXT", "created_at"),
    ("road", "updated_at", "TEXT", "created_at"),
    ("description", "updated_at", "TEXT", "created_at"),
    ("hex_inner_edge", "created_at", "TEXT", "updated_at"),
]


def migrate_schema(connection: Connection) -> None:
    for table, column, col_type, backfill_from in _COLUMN_MIGRATIONS:
        if not _has_table(connection, table) or _has_column(connection, table, column):
            continue
        try:
            # SQLite ALTER ADD only allows constant defaults, not CURRENT_TIMESTAMP.
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {col_type}",
            )
        except OperationalError as exc:
            if "duplicate column" not in str(exc).lower():
                raise
        if backfill_from and _has_column(connection, table, backfill_from):
            connection.execute(
                f"UPDATE {table} SET {column} = {backfill_from} "
                f"WHERE {column} IS NULL",
            )
        connection.execute(
            f"UPDATE {table} SET {column} = datetime('now') "
            f"WHERE {column} IS NULL",
        )
    connection.commit()


def _has_table(connection: Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _has_column(connection: Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)
