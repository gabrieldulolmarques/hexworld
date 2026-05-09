from PyQt6.QtCore import QObject, pyqtSignal

from communication.client import Client
from communication.worker import Worker
from models.session import Session

_ERROR_CODES = {
    "invalid_credentials": "Usuário ou senha inválidos.",
    "username_taken": "Nome de usuário já existe.",
    "missing_fields": "Preencha todos os campos.",
    "invalid_token": "Sessão expirada.",
    "unknown_type": "Erro de protocolo.",
}

class AuthController(QObject):
    login_success = pyqtSignal(str)
    session_restored = pyqtSignal(str)
    register_success = pyqtSignal()
    logged_out = pyqtSignal()
    error = pyqtSignal(str)
    loading = pyqtSignal(bool)

    def __init__(self, client: Client, session: Session):
        super().__init__()
        self.client = client
        self.session = session
        self.worker = None

    def login(self, username: str, password: str) -> None:
        self._send({"type": "login", "username": username, "password": password})

    def register(self, username: str, password: str) -> None:
        self._send({"type": "register", "username": username, "password": password})

    def logout(self) -> None:
        self._send({"type": "logout", "token": self.session.token})

    def validate_session(self) -> None:
        self._send({"type": "validate_session", "token": self.session.token})

    def _send(self, request: dict) -> None:
        self.loading.emit(True)
        self.worker = Worker(self.client._socket, request)
        self.worker.result_signal.connect(self._on_response)
        self.worker.error_signal.connect(self._on_network_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_response(self, response: dict) -> None:
        self.loading.emit(False)
        if response.get("status") == "error":
            code = response.get("code", "")
            if code == "invalid_token":
                self.session.clear()
            self.error.emit(_ERROR_CODES.get(code, code))
            return

        data = response.get("data", {})
        match response.get("type"):
            case "login":
                self.session.save(data["token"])
                self.session.set_user_id(data["user_id"])
                self.login_success.emit(data["user_id"])
            case "validate_session":
                self.session.set_user_id(data["user_id"])
                self.session_restored.emit(data["user_id"])
            case "register":
                self.register_success.emit()
            case "logout":
                self.session.clear()
                self.logged_out.emit()

    def _on_network_error(self, error: str) -> None:
        self.loading.emit(False)
        self.error.emit(error)
