from queue import Empty, Queue
from select import select

from PyQt6.QtCore import QThread, pyqtSignal

from transport.client import SERVER_UNREACHABLE_MESSAGE, Client
from transport.protocol import KIND_EVENT, KIND_RESPONSE

_STOP = object()

class TransportWorker(QThread):

    response = pyqtSignal(dict)
    event = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, client: Client) -> None:
        super().__init__()
        self._client = client
        self._outgoing: Queue = Queue()
        self._running = True

    def submit(self, request: dict) -> None:
        self._outgoing.put(request)

    def stop(self) -> None:
        self._running = False
        self._outgoing.put(_STOP)
        self.wait(3000)

    def run(self) -> None:
        try:
            self._client.ensure_connected()
        except Exception as exception:
            self.error.emit(str(exception))
            return

        while self._running:
            self._flush_outgoing()

            fileno = self._client.socket_fileno()
            if fileno is None:
                self.error.emit(SERVER_UNREACHABLE_MESSAGE)
                break

            readable, _, _ = select([fileno], [], [], 0.05)
            if not readable:
                continue

            try:
                frame = self._client.recv_response()
            except Exception as exception:
                self.error.emit(str(exception))
                break

            if frame is None:
                self.error.emit(SERVER_UNREACHABLE_MESSAGE)
                break

            kind = frame.get("kind")
            if kind == KIND_RESPONSE:
                self.response.emit(frame)
            elif kind == KIND_EVENT:
                self.event.emit(frame)

    def _flush_outgoing(self) -> None:
        while True:
            try:
                item = self._outgoing.get_nowait()
            except Empty:
                break
            if item is _STOP:
                self._running = False
                return
            try:
                self._client.send_request(item)
            except Exception as exception:
                self.error.emit(str(exception))
                self._running = False
                return
