from database.connection import get_connection

def get_session_by_token(token: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM session WHERE token = ?",
            (token,)
        ).fetchone()

def create_session(session_id: str, user_id: str, token: str, expires_at: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO session (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, token, expires_at)
        )
        connection.commit()

def delete_session_by_token(token: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM session WHERE token = ?",
            (token,)
        )
        connection.commit()
