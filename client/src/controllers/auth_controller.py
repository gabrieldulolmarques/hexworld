from PyQt6.QtCore import QObject, pyqtSignal

from models.limits import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from models.preferences import Preferences
from models.session import Session
from transport.sockets.worker import Worker
from transport.messages import STATUS_ERROR
from transport.sockets.protocol import request

_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid username or password.",
    "username_too_short": "Username must be at least 3 characters.",
    "username_too_long": "Username must be at most 16 characters.",
    "username_taken": "That username is already taken.",
    "missing_fields": "Missing fields.",
    "password_too_short": "Password is too short.",
    "password_too_long": "Password is too long.",
    "unknown_type": "Unknown request type.",
    "unexpected_error": "Unexpected server error.",
    "connection_lost": "Connection lost. Please try again.",
}

class AuthController(QObject):
    loading = pyqtSignal(bool)
    error = pyqtSignal(str)
    login_success = pyqtSignal(str)
    session_restored = pyqtSignal(str)
    register_success = pyqtSignal()
    logged_out = pyqtSignal()
    session_error = pyqtSignal()

    def __init__(
        self,
        worker: Worker,
        session: Session,
        preferences: Preferences,
    ) -> None:
        super().__init__()
        self._worker = worker
        self.session = session
        self.preferences = preferences
        self._pending: set[str] = set()
        self._pending_login_username = ""
        self._pending_remember = False

        worker.response.connect(self._on_response)

    def login(self, username: str, password: str, remember_me: bool = False) -> None:
        username = username.strip()
        if not username or not password:
            self.error.emit(_ERROR_MESSAGES["missing_fields"])
            return
        if len(username) > MAX_USERNAME_LENGTH:
            self.error.emit(_ERROR_MESSAGES["username_too_long"])
            return
        self._pending_login_username = username
        self._pending_remember = remember_me
        self._send(
            request(
                "login",
                {
                    "username": username,
                    "password": password,
                    "remember_me": remember_me,
                },
            )
        )

    def register(self, username: str, password: str, confirm_password: str) -> None:
        username = username.strip()
        if not username or not password or not confirm_password:
            self.error.emit(_ERROR_MESSAGES["missing_fields"])
            return
        if len(username) < MIN_USERNAME_LENGTH:
            self.error.emit(_ERROR_MESSAGES["username_too_short"])
            return
        if len(username) > MAX_USERNAME_LENGTH:
            self.error.emit(_ERROR_MESSAGES["username_too_long"])
            return
        if len(password) < MIN_PASSWORD_LENGTH:
            self.error.emit(_ERROR_MESSAGES["password_too_short"])
            return
        if len(password) > MAX_PASSWORD_LENGTH:
            self.error.emit(_ERROR_MESSAGES["password_too_long"])
            return
        if password != confirm_password:
            self.error.emit("Passwords do not match.")
            return
        self._send(
            request(
                "register",
                {
                    "username": username,
                    "password": password,
                },
            )
        )

    def logout(self) -> None:
        self._send(request("logout", {"token": self.session.token}))

    def validate_session(self) -> None:
        self._send(request("validate_session", {"token": self.session.token}))

    def handle_transport_dropped(self) -> None:
        if not self._pending:
            return
        self._pending.clear()
        self.loading.emit(False)
        self.error.emit(_ERROR_MESSAGES["connection_lost"])

    def _send(self, request: dict) -> None:
        self._pending.add(request["request_id"])
        if len(self._pending) == 1:
            self.loading.emit(True)
        if not self._worker.submit(request):
            self._pending.discard(request["request_id"])
            if not self._pending:
                self.loading.emit(False)
            self.error.emit(_ERROR_MESSAGES["unexpected_error"])

    def _on_response(self, response: dict) -> None:
        request_id = response.get("request_id", "")
        if request_id not in self._pending:
            return
        self._pending.discard(request_id)
        if not self._pending:
            self.loading.emit(False)

        if response.get("status") == STATUS_ERROR:
            code = response.get("code", "")
            if code == "invalid_token":
                self.session.clear()
                self.session_error.emit()
                return
            self.error.emit(
                _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
            )
            return

        data = response.get("data", {})
        match response.get("type"):
            case "login":
                self.session.save(data["token"])
                self.session.set_user(data["user_id"], data["username"])
                self.preferences.save(
                    self._pending_login_username,
                    self._pending_remember,
                )
                self.login_success.emit(data["username"])
            case "validate_session":
                self.session.set_user(data["user_id"], data["username"])
                self.session_restored.emit(data["username"])
            case "register":
                self.register_success.emit()
            case "logout":
                self.session.clear()
                self.logged_out.emit()
