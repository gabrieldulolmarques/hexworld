import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from repositories.session_repository import SessionRepository
from repositories.user_map_repository import UserMapRepository
from repositories.user_repository import UserRepository
from utils.passwords import hash_password, verify_password

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 16
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256

SESSION_EXPIRATION_SECONDS = 24 * 60 * 60
REMEMBER_ME_SESSION_EXPIRATION_SECONDS = 30 * 24 * 60 * 60

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        user_map_repository: UserMapRepository,
    ) -> None:
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._user_map_repository = user_map_repository

    def get_user_role(self, user_id: str, map_id: str) -> str | None:
        return self._user_map_repository.get_role(user_id, map_id)

    def register(self, username: str, password: str) -> str | None:
        if len(username) < MIN_USERNAME_LENGTH:
            return "username_too_short"
        if len(username) > MAX_USERNAME_LENGTH:
            return "username_too_long"
        if len(password) < MIN_PASSWORD_LENGTH:
            return "password_too_short"
        if len(password) > MAX_PASSWORD_LENGTH:
            return "password_too_long"
        if self._user_repository.get_user_by_username(username):
            return "username_taken"
        user_id = str(uuid4())
        password_hash = hash_password(password)
        self._user_repository.create_user(user_id, username, password_hash)
        logger.info("Registered user %r", username)
        return None

    def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> tuple[dict | None, str | None]:
        user = self._user_repository.get_user_by_username(username)
        if user is None:
            logger.warning("Login failed for unknown user %r", username)
            return None, "invalid_credentials"
        if not verify_password(password, user["password_hash"]):
            logger.warning("Login failed (bad password) for user %r", username)
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
        self._session_repository.create_session(
            session_id, user["id"], token, expires_at_text
        )
        return {
            "token": token,
            "user_id": user["id"],
            "username": user["username"],
        }, None

    def logout(self, token: str) -> str | None:
        session = self._session_repository.get_session_by_token(token)
        if session is None:
            return "invalid_token"
        self._session_repository.delete_session_by_token(token)
        return None

    def validate_session(self, token: str) -> tuple[dict | None, str | None]:
        session = self._session_repository.get_session_by_token(token)
        if session is None:
            return None, "invalid_token"
        expires_at = datetime.strptime(session["expires_at"], DATETIME_FORMAT)
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            self._session_repository.delete_session_by_token(token)
            return None, "invalid_token"
        user = self._user_repository.get_user_by_id(session["user_id"])
        if user is None:
            self._session_repository.delete_session_by_token(token)
            return None, "invalid_token"
        return {
            "user_id": user["id"],
            "username": user["username"],
        }, None
