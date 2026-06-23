from PyQt6.QtCore import QObject, pyqtSignal

from models.limits import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from models.preferences import Preferences
from models.session import Session
from rmi.worker import RemoteWorker

_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid username or password.",
    "username_too_short": "Username must be at least 3 characters.",
    "username_too_long": "Username must be at most 16 characters.",
    "username_taken": "That username is already taken.",
    "missing_fields": "Missing fields.",
    "password_too_short": "Password is too short.",
    "password_too_long": "Password is too long.",
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
        worker: RemoteWorker,
        session: Session,
        preferences: Preferences,
    ) -> None:
        super().__init__()
        self._worker = worker
        self.session = session
        self.preferences = preferences
        self._inflight = 0
        self._pending_login_username = ""
        self._pending_remember = False

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
        self._track(self._worker.login(username, password, remember_me))(
            self._on_login_ok, self._on_failed
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
        self._track(self._worker.register(username, password))(
            self._on_register_ok, self._on_failed
        )

    def logout(self) -> None:
        self._worker.logout()
        self.session.clear()
        self.logged_out.emit()

    def validate_session(self) -> None:
        call = self._worker.resume(self.session.token)
        call.succeeded.connect(self._on_resume_ok)
        call.failed.connect(self._on_resume_failed)

    def handle_transport_dropped(self) -> None:
        if self._inflight == 0:
            return
        self._inflight = 0
        self.loading.emit(False)
        self.error.emit(_ERROR_MESSAGES["connection_lost"])

    def _track(self, call):
        self._inflight += 1
        if self._inflight == 1:
            self.loading.emit(True)

        def bind(on_success, on_failure):
            call.succeeded.connect(lambda result: self._finish(on_success, result))
            call.failed.connect(lambda code: self._finish(on_failure, code))

        return bind

    def _finish(self, handler, value) -> None:
        self._inflight = max(0, self._inflight - 1)
        if self._inflight == 0:
            self.loading.emit(False)
        handler(value)

    def _on_login_ok(self, data: dict) -> None:
        self.session.save(data["token"])
        self.session.set_user(data["user_id"], data["username"])
        self.preferences.save(self._pending_login_username, self._pending_remember)
        self.login_success.emit(data["username"])

    def _on_register_ok(self, _data: dict) -> None:
        self.register_success.emit()

    def _on_failed(self, code: str) -> None:
        if code == "invalid_token":
            self.session.clear()
            self.session_error.emit()
            return
        self.error.emit(_ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"]))

    def _on_resume_ok(self, data: dict) -> None:
        self.session.set_user(data["user_id"], data["username"])
        self.session_restored.emit(data["username"])

    def _on_resume_failed(self, code: str) -> None:
        if code == "invalid_token":
            self.session.clear()
            self.session_error.emit()
