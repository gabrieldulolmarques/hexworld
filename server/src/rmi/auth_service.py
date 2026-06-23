import logging

import Pyro5.api

from rmi.context import RmiContext
from rmi.errors import HexworldError
from rmi.session import Session

logger = logging.getLogger(__name__)

@Pyro5.api.expose
class AuthService:
    """Bootstrap object registered in the Name Server. Factory for Session objects."""

    def __init__(self, context: RmiContext) -> None:
        self._ctx = context

    def register(self, username: str, password: str) -> None:
        username = str(username or "").strip()
        password = str(password or "")
        if not username or not password:
            raise HexworldError("missing_fields")
        error = self._ctx.auth_service.register(username, password)
        if error:
            raise HexworldError(error)

    def login(self, username: str, password: str, remember_me: bool = False) -> Session:
        username = str(username or "").strip()
        password = str(password or "")
        if not username or not password:
            raise HexworldError("missing_fields")
        data, error = self._ctx.auth_service.login(username, password, bool(remember_me))
        if error:
            raise HexworldError(error)
        logger.info("Login for user %r (RMI)", data["username"])
        return self._make_session(data["token"], data["user_id"], data["username"])

    def resume(self, token: str) -> Session:
        token = str(token or "").strip()
        if not token:
            raise HexworldError("missing_fields")
        data, error = self._ctx.auth_service.validate_session(token)
        if error:
            raise HexworldError(error)
        existing = self._ctx.registry.get(token)
        if existing is not None:
            return existing
        return self._make_session(token, data["user_id"], data["username"])

    @Pyro5.api.oneway
    def disconnect(self, token: str) -> None:
        session = self._ctx.registry.get(str(token or "").strip())
        if session is not None:
            session.cleanup()

    def _make_session(self, token: str, user_id: str, username: str) -> Session:
        session = Session(self._ctx, token, user_id, username)
        self._ctx.daemon.register(session)
        self._ctx.registry.add(token, session)
        return session
