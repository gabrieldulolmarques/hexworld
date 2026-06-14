import logging
from sqlite3 import Connection

from utils.passwords import hash_password

logger = logging.getLogger(__name__)

DEFAULT_USERS = [
    ("00000000-0000-0000-0000-000000000001", "user1", "password1"),
    ("00000000-0000-0000-0000-000000000002", "user2", "password2"),
    ("00000000-0000-0000-0000-000000000003", "user3", "password3"),
    ("00000000-0000-0000-0000-000000000004", "user4", "password4"),
]

def seed_users(connection: Connection) -> None:
    users = [
        (user_id, username, hash_password(password))
        for user_id, username, password in DEFAULT_USERS
    ]
    try:
        connection.executemany(
            """
            INSERT OR IGNORE INTO user (id, username, password_hash)
            VALUES (?, ?, ?)
            """,
            users,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        logger.exception("Error seeding users")
        raise
