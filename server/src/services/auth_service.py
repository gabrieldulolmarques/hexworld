from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from repositories.session_repository import (
    create_session,
    delete_session_by_token,
    get_session_by_token,
)
from repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_user_by_username,
)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256

SESSION_EXPIRATION_SECONDS = 24 * 60 * 60
REMEMBER_ME_SESSION_EXPIRATION_SECONDS = 30 * 24 * 60 * 60

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()

def register(username: str, password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return "password_too_short"
    if len(password) > MAX_PASSWORD_LENGTH:
        return "password_too_long"
    if get_user_by_username(username):
        return "username_taken"
    user_id = str(uuid4())
    password_hash = hash_password(password)
    try:
        create_user(user_id, username, password_hash)
    except Exception:
        return "username_taken"
    return None

def login(
    username: str,
    password: str,
    remember_me: bool = False,
) -> tuple[dict | None, str | None]:
    user = get_user_by_username(username)
    if user is None:
        return None, "invalid_credentials"
    password_hash = hash_password(password)
    if user["password_hash"] != password_hash:
        return None, "invalid_credentials"
    session_id = str(uuid4())
    token = str(uuid4())
    expiration_seconds = (
        REMEMBER_ME_SESSION_EXPIRATION_SECONDS
        if remember_me
        else SESSION_EXPIRATION_SECONDS
    )
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds)
    expires_at_text = expires_at.strftime(DATETIME_FORMAT)
    create_session(
        session_id,
        user["id"],
        token,
        expires_at_text,
    )
    return {
        "token": token,
        "user_id": user["id"],
        "username": user["username"],
    }, None

def logout(token: str) -> str | None:
    session = get_session_by_token(token)
    if session is None:
        return "invalid_token"
    delete_session_by_token(token)
    return None

def validate_session(token: str) -> tuple[dict | None, str | None]:
    session = get_session_by_token(token)
    if session is None:
        return None, "invalid_token"
    expires_at = datetime.strptime(session["expires_at"], DATETIME_FORMAT)
    expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        delete_session_by_token(token)
        return None, "invalid_token"
    user = get_user_by_id(session["user_id"])
    if user is None:
        delete_session_by_token(token)
        return None, "invalid_token"
    return {
        "user_id": user["id"],
        "username": user["username"],
    }, None
