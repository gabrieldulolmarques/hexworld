from database.connection import get_connection

class MapRepository:
    def create_map(
        self, map_id: str, name: str, editor_code: str, viewer_code: str
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO map (id, name, editor_code, viewer_code) VALUES (?, ?, ?, ?)",
                (map_id, name, editor_code, viewer_code),
            )
            connection.commit()

    def get_map_by_id(self, map_id: str):
        with get_connection() as connection:
            return connection.execute(
                "SELECT * FROM map WHERE id = ?",
                (map_id,),
            ).fetchone()

    def get_map_by_code(self, code: str) -> tuple[str, str] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM map WHERE editor_code = ?",
                (code,),
            ).fetchone()
            if row is not None:
                return row["id"], "editor"
            row = connection.execute(
                "SELECT id FROM map WHERE viewer_code = ?",
                (code,),
            ).fetchone()
            if row is not None:
                return row["id"], "viewer"
            return None

    def delete_map(self, map_id: str) -> None:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM user_map WHERE map_id = ?", (map_id,))
            connection.execute("DELETE FROM map WHERE id = ?", (map_id,))
            connection.commit()

    def list_maps_for_user(self, user_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT map.id, map.name, map.editor_code, map.viewer_code, map.created_at,
                       user_map.role,
                       (SELECT COUNT(*) FROM user_map WHERE map_id = map.id) member_count
                FROM map
                JOIN user_map ON user_map.map_id = map.id
                WHERE user_map.user_id = ?
                ORDER BY map.created_at DESC
                """,
                (user_id,),
            ).fetchall()
