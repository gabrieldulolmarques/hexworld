from database.connection import get_connection

def get_user_by_username(username: str):
    connection = get_connection()
    return connection.execute(
        "SELECT * FROM user WHERE username = ?",
        (username,)
    ).fetchone()

def get_user_by_id(user_id: str):
    connection = get_connection()
    return connection.execute(
        "SELECT * FROM user WHERE id = ?",
        (user_id,)
    ).fetchone()

def create_user(user_id: str, username: str, password_hash: str) -> None:
    connection = get_connection()
    connection.execute(
        "INSERT INTO user (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash)
    )
    connection.commit()
