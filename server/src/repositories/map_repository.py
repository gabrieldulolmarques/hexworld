from database.connection import get_connection

def create_map(map_id: str, name: str, editor_code: str, viewer_code: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO map (id, name, editor_code, viewer_code) VALUES (?, ?, ?, ?)",
            (map_id, name, editor_code, viewer_code),
        )
        connection.commit()

def get_map_by_id(map_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM map WHERE id = ?",
            (map_id,),
        ).fetchone()

def get_map_by_code(code: str) -> tuple[str, str] | None:
    """Resolve a share code to (map_id, role) where role is 'editor' or 'viewer'."""
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

def list_maps_for_user(user_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT m.id, m.name, m.editor_code, m.viewer_code, m.created_at, um.role
            FROM map AS m
            JOIN user_map AS um ON um.map_id = m.id
            WHERE um.user_id = ?
            ORDER BY m.created_at DESC
            """,
            (user_id,),
        ).fetchall()
