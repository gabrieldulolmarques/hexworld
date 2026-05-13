from PyQt6.QtCore import QThread, pyqtSignal

from transport.client import Client

class RequestWorker(QThread):

    response = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, client: Client, request: dict) -> None:
        super().__init__()
        self.client = client
        self.request = request

    def run(self) -> None:
        try:
            response = self.client.send(self.request)
            self.response.emit(response)
        except Exception as exception:
            self.error.emit(str(exception))
