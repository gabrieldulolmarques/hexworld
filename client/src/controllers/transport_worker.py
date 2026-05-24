from queue import Empty, Queue
from select import select
from traceback import format_exc

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
        self._alive = True

    def submit(self, request: dict) -> bool:
        if not self._alive:
            return False
        self._outgoing.put(request)
        return True

    def reset(self) -> None:
        while not self._outgoing.empty():
            try:
                self._outgoing.get_nowait()
            except Empty:
                break
        self._running = True
        self._alive = True

    def stop(self) -> None:
        self._running = False
        self._alive = False
        self._outgoing.put(_STOP)
        self.wait(3000)

    def run(self) -> None:
        try:
            self._client.ensure_connected()
        except Exception as exception:
            print(f"Error connecting to server: {exception}")
            print(format_exc())
            self._fail(str(exception))
            return

        while self._running:
            self._flush_outgoing()
            if not self._running:
                break

            fileno = self._client.socket_fileno()
            if fileno is None:
                self._fail(SERVER_UNREACHABLE_MESSAGE)
                break

            try:
                readable, _, _ = select([fileno], [], [], 0.05)
            except OSError:
                self._fail(SERVER_UNREACHABLE_MESSAGE)
                break
            if not readable:
                continue

            try:
                frame = self._client.recv_response()
            except Exception as exception:
                print(f"Error reading frame from server: {exception}")
                print(format_exc())
                self._fail(str(exception))
                break

            if frame is None:
                self._fail(SERVER_UNREACHABLE_MESSAGE)
                break

            kind = frame.get("kind")
            if kind == KIND_RESPONSE:
                self.response.emit(frame)
            elif kind == KIND_EVENT:
                self.event.emit(frame)
            else:
                print(f"Error processing frame: unknown kind={kind!r}")

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
                print(f"Error sending request to server: {exception}")
                print(format_exc())
                self._fail(str(exception))
                return

    def _fail(self, message: str) -> None:
        self._alive = False
        self._running = False
        self.error.emit(message)
