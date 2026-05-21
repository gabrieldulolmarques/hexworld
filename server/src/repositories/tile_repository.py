from uuid import uuid4

from database.connection import get_connection

def get_or_create_tile(map_id: str, q: int, r: int) -> str:
    """Return the tile id at (map_id, q, r), creating the row if absent. Covers RF19."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM tile WHERE map_id = ? AND q = ? AND r = ?",
            (map_id, q, r),
        ).fetchone()
        if row is not None:
            return row["id"]
        tile_id = str(uuid4())
        connection.execute(
            "INSERT INTO tile (id, map_id, q, r) VALUES (?, ?, ?, ?)",
            (tile_id, map_id, q, r),
        )
        connection.commit()
        return tile_id

def get_tile_by_id(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, map_id, q, r FROM tile WHERE id = ?",
            (tile_id,),
        ).fetchone()


def delete_tile(tile_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM tile WHERE id = ?", (tile_id,))
        connection.commit()


def list_tiles_with_components(map_id: str) -> list[dict]:
    """Serialize the full map state for RF09.

    Returns one dict per tile that has at least one component, with structure /
    roads / description nested. Empty tiles are omitted (RF19 keeps them implicit).
    """
    with get_connection() as connection:
        tiles = connection.execute(
            "SELECT id, q, r FROM tile WHERE map_id = ?",
            (map_id,),
        ).fetchall()
        if not tiles:
            return []
        tile_ids = [t["id"] for t in tiles]
        placeholders = ",".join("?" * len(tile_ids))
        structures = {
            row["tile_id"]: dict(row)
            for row in connection.execute(
                f"SELECT tile_id, type, author_id, created_at FROM structure WHERE tile_id IN ({placeholders})",
                tile_ids,
            ).fetchall()
        }
        descriptions = {
            row["tile_id"]: dict(row)
            for row in connection.execute(
                f"SELECT tile_id, text, author_id, created_at FROM description WHERE tile_id IN ({placeholders})",
                tile_ids,
            ).fetchall()
        }
        roads_by_tile: dict[str, list[dict]] = {}
        for row in connection.execute(
            f"SELECT id, tile_id, color, author_id, created_at FROM road WHERE tile_id IN ({placeholders})",
            tile_ids,
        ).fetchall():
            roads_by_tile.setdefault(row["tile_id"], []).append(dict(row))
        result = []
        for tile in tiles:
            tile_id = tile["id"]
            structure = structures.get(tile_id)
            description = descriptions.get(tile_id)
            roads = roads_by_tile.get(tile_id, [])
            if not structure and not description and not roads:
                continue
            result.append({
                "q": tile["q"],
                "r": tile["r"],
                "structure": structure,
                "description": description,
                "roads": roads,
            })
        return result
