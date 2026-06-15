from database.connection import get_connection

class DescriptionRepository:
    def get_description(self, tile_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT tile_id, text, author_id, created_at, updated_at
                FROM description WHERE tile_id = ?
                """,
                (tile_id,),
            ).fetchone()

    def upsert_description(self, tile_id: str, text: str, author_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO description (tile_id, text, author_id)
                VALUES (?, ?, ?)
                ON CONFLICT(tile_id) DO UPDATE SET
                    text = excluded.text,
                    author_id = excluded.author_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (tile_id, text, author_id),
            )
            connection.commit()

    def delete_description(self, tile_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM description WHERE tile_id = ?", (tile_id,)
            )
            connection.commit()
