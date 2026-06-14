from database.connection import get_connection

class UserRepository:
    def get_user_by_username(self, username: str):
        with get_connection() as connection:
            return connection.execute(
                "SELECT * FROM user WHERE username = ?", (username,)
            ).fetchone()

    def get_user_by_id(self, user_id: str):
        with get_connection() as connection:
            return connection.execute(
                "SELECT * FROM user WHERE id = ?", (user_id,)
            ).fetchone()

    def get_users_by_ids(self, user_ids: list[str]) -> dict[str, str]:
        if not user_ids:
            return {}
        with get_connection() as connection:
            placeholders = ",".join("?" * len(user_ids))
            rows = connection.execute(
                f"SELECT id, username FROM user WHERE id IN ({placeholders})",
                user_ids,
            ).fetchall()
        return {row["id"]: row["username"] for row in rows}

    def create_user(self, user_id: str, username: str, password_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO user (id, username, password_hash) VALUES (?, ?, ?)",
                (user_id, username, password_hash),
            )
            connection.commit()
