from hashlib import sha256
from sqlite3 import Connection

DEFAULT_USERS = [
    ("00000000-0000-0000-0000-000000000001", "user1", "user1"),
    ("00000000-0000-0000-0000-000000000002", "user2", "user2"),
    ("00000000-0000-0000-0000-000000000003", "user3", "user3"),
    ("00000000-0000-0000-0000-000000000004", "user4", "user4"),
]

def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()

def seed_users(connection: Connection) -> None:
    users = [
        (user_id, username, hash_password(password))
        for user_id, username, password in DEFAULT_USERS
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO user (id, username, password_hash)
        VALUES (?, ?, ?)
        """,
        users,
    )
    connection.commit()
