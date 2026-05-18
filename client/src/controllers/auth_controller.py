from PyQt6.QtCore import QObject, pyqtSignal

from controllers.transport_worker import TransportWorker
from models.preferences import Preferences
from models.session import Session
from transport.protocol import request

_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid username or password.",
    "username_taken": "That username is already taken.",
    "missing_fields": "Missing fields.",
    "password_too_short": "Password is too short.",
    "password_too_long": "Password is too long.",
    "invalid_token": "Session expired.",
    "unknown_type": "Unknown request type.",
    "unexpected_error": "Unexpected server error.",
}

class AuthController(QObject):

    loading = pyqtSignal(bool)
    error = pyqtSignal(str)
    login_success = pyqtSignal(str)
    session_restored = pyqtSignal(str)
    register_success = pyqtSignal()
    logged_out = pyqtSignal()
    session_expired = pyqtSignal()

    def __init__(
        self,
        transport_worker: TransportWorker,
        session: Session,
        preferences: Preferences,
    ) -> None:
        super().__init__()
        self._transport_worker = transport_worker
        self.session = session
        self.preferences = preferences
        self._pending: set[str] = set()
        self._pending_login_username = ""
        self._pending_remember = False

        transport_worker.response.connect(self._on_response)
        transport_worker.error.connect(self._on_error)

    def login(self, username: str, password: str, remember_me: bool = False) -> None:
        username = username.strip()
        if not username or not password:
            self.error.emit("Missing fields.")
            return
        self._pending_login_username = username
        self._pending_remember = remember_me
        self._send(request("login", {
            "username": username,
            "password": password,
            "remember_me": remember_me,
        }))

    def register(self, username: str, password: str, confirm_password: str) -> None:
        username = username.strip()
        if not username or not password or not confirm_password:
            self.error.emit("Missing fields.")
            return
        if password != confirm_password:
            self.error.emit("Passwords do not match.")
            return
        self._send(request("register", {
            "username": username,
            "password": password,
        }))

    def logout(self) -> None:
        self._send(request("logout", {"token": self.session.token}))

    def validate_session(self) -> None:
        self._send(request("validate_session", {"token": self.session.token}))

    def _send(self, request: dict) -> None:
        self._pending.add(request["request_id"])
        if len(self._pending) == 1:
            self.loading.emit(True)
        self._transport_worker.submit(request)

    def _on_response(self, response: dict) -> None:
        request_id = response.get("request_id", "")
        if request_id not in self._pending:
            return
        self._pending.discard(request_id)
        if not self._pending:
            self.loading.emit(False)

        if response.get("status") == "error":
            code = response.get("code", "")
            if code == "invalid_token":
                self.session.clear()
                self.session_expired.emit()
            self.error.emit(_ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"]))
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

    def _on_error(self, message: str) -> None:
        had_pending = bool(self._pending)
        self._pending.clear()
        if had_pending:
            self.loading.emit(False)
        self.error.emit(message)
