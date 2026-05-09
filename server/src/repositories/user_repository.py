from sqlite3 import Connection
from time import time

def get_user_by_username(connection: Connection, username: str):
    return connection.execute(
        "SELECT * FROM user WHERE username = ?",
        (username,)
    ).fetchone()

def create_user(connection: Connection, user_id: str, username: str, password_hash: str) -> None:
    connection.execute(
        "INSERT INTO user (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash)
    )
    connection.commit()

def get_session_by_token(connection: Connection, token: str):
    return connection.execute(
        "SELECT * FROM session WHERE token = ? AND expires_at > ?",
        (token, int(time()))
    ).fetchone()

def create_session(connection: Connection, session_id: str, user_id: str, token: str, expires_at: int) -> None:
    connection.execute(
        "INSERT INTO session (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, token, expires_at)
    )
    connection.commit()

def delete_session_by_token(connection: Connection, token: str) -> None:
    connection.execute(
        "DELETE FROM session WHERE token = ?",
        (token,)
    )
    connection.commit()
