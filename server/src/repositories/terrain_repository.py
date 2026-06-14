from database.connection import get_connection

class TerrainRepository:
    def get_terrain(self, tile_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT tile_id, type, author_id, created_at, updated_at
                FROM terrain WHERE tile_id = ?
                """,
                (tile_id,),
            ).fetchone()

    def upsert_terrain(self, tile_id: str, terrain_type: str, author_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO terrain (tile_id, type, author_id)
                VALUES (?, ?, ?)
                ON CONFLICT(tile_id) DO UPDATE SET
                    type = excluded.type,
                    author_id = excluded.author_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (tile_id, terrain_type, author_id),
            )
            connection.commit()

    def delete_terrain(self, tile_id: str) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM terrain WHERE tile_id = ?", (tile_id,))
            connection.commit()
