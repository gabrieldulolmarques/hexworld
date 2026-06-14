from uuid import uuid4

from database.connection import get_connection

class TileRepository:
    def get_or_create_tile(self, map_id: str, q: int, r: int) -> str:
        # INSERT OR IGNORE avoids SELECT-then-INSERT race when two threads
        # target the same coordinate simultaneously.
        tile_id = str(uuid4())
        with get_connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO tile (id, map_id, q, r) VALUES (?, ?, ?, ?)",
                (tile_id, map_id, q, r),
            )
            connection.commit()
            row = connection.execute(
                "SELECT id FROM tile WHERE map_id = ? AND q = ? AND r = ?",
                (map_id, q, r),
            ).fetchone()
            return row["id"]

    def get_tile_by_id(self, tile_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, map_id, q, r, created_at, updated_at
                FROM tile WHERE id = ?
                """,
                (tile_id,),
            ).fetchone()

    def touch_tile(self, tile_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE tile SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (tile_id,),
            )
            connection.commit()

    def get_tile_at(self, map_id: str, q: int, r: int):
        with get_connection() as connection:
            return connection.execute(
                "SELECT id, map_id, q, r FROM tile WHERE map_id = ? AND q = ? AND r = ?",
                (map_id, q, r),
            ).fetchone()

    def list_tiles_with_components(self, map_id: str) -> list[dict]:
        with get_connection() as connection:
            tiles = connection.execute(
                "SELECT id, q, r FROM tile WHERE map_id = ?",
                (map_id,),
            ).fetchall()
            if not tiles:
                return []
            tile_ids = [t["id"] for t in tiles]
            placeholders = ",".join("?" * len(tile_ids))
            terrains = {
                row["tile_id"]: dict(row)
                for row in connection.execute(
                    f"""
                    SELECT tile_id, type, author_id, created_at, updated_at
                    FROM terrain WHERE tile_id IN ({placeholders})
                    """,
                    tile_ids,
                ).fetchall()
            }
            descriptions = {
                row["tile_id"]: dict(row)
                for row in connection.execute(
                    f"""
                    SELECT tile_id, text, author_id, created_at, updated_at
                    FROM description WHERE tile_id IN ({placeholders})
                    """,
                    tile_ids,
                ).fetchall()
            }
            result = []
            for tile in tiles:
                tile_id = tile["id"]
                terrain = terrains.get(tile_id)
                description = descriptions.get(tile_id)
                if not terrain and not description:
                    continue
                result.append(
                    {
                        "tile_id": tile_id,
                        "q": tile["q"],
                        "r": tile["r"],
                        "terrain": terrain,
                        "description": description,
                    }
                )
            return result
