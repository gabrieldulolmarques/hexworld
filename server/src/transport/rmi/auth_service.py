import logging

import Pyro5.api

from services.auth_service import AuthService as DomainAuthService
from transport.rmi.base import _RemoteBase
from transport.rmi.session_registry import RmiSessionRegistry

logger = logging.getLogger(__name__)


@Pyro5.api.expose
class AuthService(_RemoteBase):
    def __init__(
        self,
        handle_request,
        registry: RmiSessionRegistry,
        domain_auth: DomainAuthService,
    ) -> None:
        super().__init__(handle_request, registry)
        self._domain_auth = domain_auth

    def register(self, username: str, password: str) -> dict:
        return self._anon_call(
            "register", {"username": username, "password": password}
        )

    def login(self, username: str, password: str, remember_me: bool = False) -> dict:
        return self._anon_call(
            "login",
            {"username": username, "password": password, "remember_me": remember_me},
        )

    def validate_session(self, token: str) -> dict:
        return self._auth_call("validate_session", token, {})

    def logout(self, token: str) -> dict:
        response = self._auth_call("logout", token, {})
        self._registry.remove(str(token or "").strip())
        return response

    @Pyro5.api.oneway
    def disconnect(self, token: str) -> None:
        # Graceful teardown when the client window closes: drop the in-memory
        # session (unsubscribe, leave presence, broadcast offline) without
        # invalidating the persisted auth token, so "remember me" still works.
        self._registry.remove(str(token or "").strip())

    def register_event_callback(self, token: str, callback_uri: str) -> None:
        token = str(token or "").strip()
        callback_uri = str(callback_uri or "").strip()
        if not token or not callback_uri:
            raise ValueError("token and callback_uri are required")

        user_data, error_code = self._domain_auth.validate_session(token)
        if error_code:
            raise ValueError(error_code)

        session = self._registry.get_or_create(token)
        session.bind_user(user_data["user_id"], user_data["username"])
        session.set_event_callback(callback_uri)
        logger.debug("Registered event callback for user %r", user_data["username"])
