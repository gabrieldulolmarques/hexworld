from database.connection import get_connection

class EdgeRepository:
    def list_edges_for_map(self, map_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT map_id, q, r, edges, color, author_id, created_at, updated_at
                FROM edge
                WHERE map_id = ?
                """,
                (map_id,),
            ).fetchall()

    def get_edge_tile(self, map_id: str, q: int, r: int):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT map_id, q, r, edges, color, author_id, created_at, updated_at
                FROM edge
                WHERE map_id = ? AND q = ? AND r = ?
                """,
                (map_id, q, r),
            ).fetchone()

    def upsert_edge_tile(
        self,
        map_id: str,
        q: int,
        r: int,
        edges: int,
        color: str,
        author_id: str,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO edge (map_id, q, r, edges, color, author_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(map_id, q, r) DO UPDATE SET
                    edges = excluded.edges,
                    color = excluded.color,
                    author_id = excluded.author_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (map_id, q, r, edges, color, author_id),
            )
            connection.commit()

    def delete_edge_tile(self, map_id: str, q: int, r: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM edge WHERE map_id = ? AND q = ? AND r = ?",
                (map_id, q, r),
            )
            connection.commit()
