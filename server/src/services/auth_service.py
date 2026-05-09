from hashlib import sha256
from time import time
from uuid import uuid4

from database.connection import get_connection
from repositories.user_repository import (
    create_session,
    create_user,
    delete_session_by_token,
    get_session_by_token,
    get_user_by_username,
)

SESSION_EXPIRATION_TIME = 24 * 60 * 60
SESSION_EXPIRATION_TIME_REMEMBER_ME = 30 * 24 * 60 * 60

def _hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()

def register(username: str, password: str) -> dict:
    connection = get_connection()
    if get_user_by_username(connection, username):
        return {"type": "register", "status": "error", "code": "username_taken"}
    create_user(connection, str(uuid4()), username, _hash_password(password))
    return {"type": "register", "status": "ok"}

def login(username: str, password: str, remember_me: bool = False) -> dict:
    connection = get_connection()
    user = get_user_by_username(connection, username)
    if not user or user["password_hash"] != _hash_password(password):
        return {"type": "login", "status": "error", "code": "invalid_credentials"}
    token = str(uuid4())
    expires_at = int(time()) + (SESSION_EXPIRATION_TIME_REMEMBER_ME if remember_me else SESSION_EXPIRATION_TIME)
    create_session(connection, str(uuid4()), user["id"], token, expires_at)
    return {"type": "login", "status": "ok", "data": {"token": token, "user_id": user["id"]}}

def logout(token: str) -> dict:
    connection = get_connection()
    if not get_session_by_token(connection, token):
        return {"type": "logout", "status": "error", "code": "invalid_token"}
    delete_session_by_token(connection, token)
    return {"type": "logout", "status": "ok"}

def validate_session(token: str) -> dict:
    connection = get_connection()
    session = get_session_by_token(connection, token)
    if not session:
        return {"type": "validate_session", "status": "error", "code": "invalid_token"}
    return {"type": "validate_session", "status": "ok", "data": {"user_id": session["user_id"]}}
