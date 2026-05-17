from PyQt6.QtCore import QObject, pyqtSignal

from controllers.request_worker import RequestWorker
from models.preferences import Preferences
from models.session import Session
from transport.client import Client

_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid username or password.",
    "username_taken": "That username is already taken.",
    "missing_fields": "Missing fields.",
    "password_too_short": "Password is too short.",
    "password_too_long": "Password is too long.",
    "invalid_token": "Session expired.",
    "unknown_type": "Unknown request type.",
}

_UNEXPECTED_ERROR = "Unexpected server error."

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
        client: Client,
        session: Session,
        preferences: Preferences,
    ) -> None:
        super().__init__()
        self.client = client
        self.session = session
        self.preferences = preferences
        self._worker: RequestWorker | None = None
        self._pending_login_username = ""
        self._pending_remember = False

    def login(self, username: str, password: str, remember_me: bool = False) -> None:
        username = username.strip()
        if not username or not password:
            self.error.emit("Missing fields.")
            return
        self._pending_login_username = username
        self._pending_remember = remember_me
        self._send({
            "type": "login",
            "data": {
                "username": username,
                "password": password,
                "remember_me": remember_me,
            },
        })

    def register(self, username: str, password: str, confirm_password: str) -> None:
        username = username.strip()
        if not username or not password or not confirm_password:
            self.error.emit("Missing fields.")
            return
        if password != confirm_password:
            self.error.emit("Passwords do not match.")
            return
        self._send({
            "type": "register",
            "data": {
                "username": username,
                "password": password,
            },
        })

    def logout(self) -> None:
        self._send({"type": "logout", "data": {"token": self.session.token}})

    def validate_session(self) -> None:
        self._send({"type": "validate_session", "data": {"token": self.session.token}})

    def _send(self, request: dict) -> None:
        self.loading.emit(True)
        self._worker = RequestWorker(self.client, request)
        self._worker.response.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_response(self, response: dict) -> None:
        self.loading.emit(False)

        if response.get("status") == "error":
            code = response.get("code", "")
            if code == "invalid_token":
                self.session.clear()
                self.session_expired.emit()
            self.error.emit(_ERROR_MESSAGES.get(code, _UNEXPECTED_ERROR))
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
        self.loading.emit(False)
        self.error.emit(message)
