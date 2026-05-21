from uuid import uuid4

from database.connection import get_connection

def get_structure(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT tile_id, type, author_id, created_at FROM structure WHERE tile_id = ?",
            (tile_id,),
        ).fetchone()

def upsert_structure(tile_id: str, structure_type: str, author_id: str) -> None:
    """One structure per tile (RF12). ON CONFLICT keeps the primary key stable."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO structure (tile_id, type, author_id)
            VALUES (?, ?, ?)
            ON CONFLICT(tile_id) DO UPDATE SET
                type = excluded.type,
                author_id = excluded.author_id,
                created_at = CURRENT_TIMESTAMP
            """,
            (tile_id, structure_type, author_id),
        )
        connection.commit()

def add_road(tile_id: str, color: str, author_id: str) -> str:
    """Roads are multi-per-tile, identified by color (RF13). Returns the new road id."""
    road_id = str(uuid4())
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO road (id, tile_id, color, author_id) VALUES (?, ?, ?, ?)",
            (road_id, tile_id, color, author_id),
        )
        connection.commit()
    return road_id

def list_roads(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, color, author_id, created_at FROM road WHERE tile_id = ?",
            (tile_id,),
        ).fetchall()

def get_description(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT tile_id, text, author_id, created_at FROM description WHERE tile_id = ?",
            (tile_id,),
        ).fetchone()

def upsert_description(tile_id: str, text: str, author_id: str) -> None:
    """One description per tile (RF14)."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO description (tile_id, text, author_id)
            VALUES (?, ?, ?)
            ON CONFLICT(tile_id) DO UPDATE SET
                text = excluded.text,
                author_id = excluded.author_id,
                created_at = CURRENT_TIMESTAMP
            """,
            (tile_id, text, author_id),
        )
        connection.commit()

def get_road_by_id(road_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, tile_id, color, author_id FROM road WHERE id = ?",
            (road_id,),
        ).fetchone()


def delete_road(road_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM road WHERE id = ?", (road_id,))
        connection.commit()


def delete_description(tile_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM description WHERE tile_id = ?", (tile_id,))
        connection.commit()


def get_cell_details(tile_id: str) -> dict:
    """Aggregate structure / roads / description for RF10."""
    structure = get_structure(tile_id)
    description = get_description(tile_id)
    roads = list_roads(tile_id)
    return {
        "structure": dict(structure) if structure else None,
        "description": dict(description) if description else None,
        "roads": [dict(r) for r in roads],
    }
