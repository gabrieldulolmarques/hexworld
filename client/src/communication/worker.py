from PyQt6.QtCore import QThread, pyqtSignal

from communication.protocol import recv_response, send_request


class Worker(QThread):

    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, client, request: dict):
        super().__init__()
        self.client = client
        self.request = request

    def run(self) -> None:
        try:
            send_request(self.client, self.request)
            response = recv_response(self.client)
            if response is None:
                self.error_signal.emit("No response from server")
                return
            self.result_signal.emit(response)
        except Exception as exception:
            self.error_signal.emit(str(exception))
