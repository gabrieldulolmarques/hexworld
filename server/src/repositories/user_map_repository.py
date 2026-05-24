from database.connection import get_connection

def add_user_to_map(user_id: str, map_id: str, role: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO user_map (user_id, map_id, role)
            VALUES (?, ?, ?)
            """,
            (user_id, map_id, role),
        )
        connection.commit()

def get_role(user_id: str, map_id: str) -> str | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT role FROM user_map WHERE user_id = ? AND map_id = ?",
            (user_id, map_id),
        ).fetchone()
        return row["role"] if row is not None else None

def list_members(map_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT um.user_id, u.username, um.role, um.created_at
            FROM user_map AS um
            JOIN user AS u ON u.id = um.user_id
            WHERE um.map_id = ?
            """,
            (map_id,),
        ).fetchall()

def remove_user_from_map(user_id: str, map_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM user_map WHERE user_id = ? AND map_id = ?",
            (user_id, map_id),
        )
        connection.commit()

def transfer_ownership(map_id: str, from_user_id: str, to_user_id: str) -> None:
    with get_connection() as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM user_map WHERE map_id = ? AND user_id = ?",
                (map_id, from_user_id),
            )
            connection.execute(
                """
                UPDATE user_map
                SET role = 'owner', updated_at = CURRENT_TIMESTAMP
                WHERE map_id = ? AND user_id = ?
                """,
                (map_id, to_user_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
