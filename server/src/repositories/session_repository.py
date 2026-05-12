from database.connection import get_connection

def get_session_by_token(token: str):
    connection = get_connection()
    return connection.execute(
        "SELECT * FROM session WHERE token = ?",
        (token,)
    ).fetchone()

def create_session(session_id: str, user_id: str, token: str, expires_at: str) -> None:
    connection = get_connection()
    connection.execute(
        "INSERT INTO session (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, token, expires_at)
    )
    connection.commit()

def delete_session_by_token(token: str) -> None:
    connection = get_connection()
    connection.execute(
        "DELETE FROM session WHERE token = ?",
        (token,)
    )
    connection.commit()
