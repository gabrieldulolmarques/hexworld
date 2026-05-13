from PyQt6.QtCore import QObject, pyqtSignal

from controllers.request_worker import RequestWorker
from transport.client import Client

_ERROR_CODES = {
    "unknown_type": "Unknown request type.",
}

_UNEXPECTED_ERROR = "Unexpected server error."

class BaseController(QObject):

    loading = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self._worker: RequestWorker | None = None

    def _send(self, request: dict) -> None:
        self.loading.emit(True)
        self._worker = RequestWorker(self.client, request)
        self._worker.response.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_response(self, response: dict) -> None:
        self.loading.emit(False)

    def _on_error(self, message: str) -> None:
        self.loading.emit(False)
        self.error.emit(message)

    def _translate_error(
        self,
        code: str,
        error_codes: dict[str, str] | None = None,
    ) -> str:
        if error_codes and code in error_codes:
            return error_codes[code]
        if code in _ERROR_CODES:
            return _ERROR_CODES[code]
        return _UNEXPECTED_ERROR
