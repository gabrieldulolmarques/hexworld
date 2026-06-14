import Pyro5.api

from transport.rmi.base import _RemoteBase


@Pyro5.api.expose
class AuthService(_RemoteBase):
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
        self._registry.remove(token)
        return response

    def register_event_callback(self, token: str, callback_uri: str) -> None:
        self._registry.get_or_create(token).set_event_callback(callback_uri)
