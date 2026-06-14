import logging
import time
from queue import Empty, Queue
from select import select
from traceback import format_exc

from PyQt6.QtCore import QThread, pyqtSignal

from transport.client import Client
from transport.protocol import KIND_EVENT, KIND_RESPONSE

logger = logging.getLogger(__name__)

_STOP = object()
RECONNECT_DELAY_S = 2.0

class TransportWorker(QThread):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    response = pyqtSignal(dict)
    event = pyqtSignal(dict)

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
        self._client.stop()
        self.wait(3000)

    def run(self) -> None:
        was_connected = False
        while self._running:
            try:
                self._client.ensure_connected()
            except Exception as exception:
                logger.warning("Error connecting to server: %s", exception)
                logger.debug(format_exc())
                if was_connected:
                    was_connected = False
                    self.disconnected.emit()
                self._sleep_reconnect()
                continue

            if not was_connected:
                was_connected = True
                self.connected.emit()

            if self._serve_until_disconnect():
                break

            self._client.stop()
            if was_connected:
                was_connected = False
                self.disconnected.emit()
            if not self._running:
                break
            self._sleep_reconnect()

    def _serve_until_disconnect(self) -> bool:
        """Return True when the worker should exit cleanly."""
        while self._running:
            if not self._flush_outgoing():
                return False

            fileno = self._client.socket_fileno()
            if fileno is None:
                return False

            try:
                readable, _, _ = select([fileno], [], [], 0.05)
            except OSError:
                return False
            if not readable:
                continue

            try:
                frame = self._client.recv_response()
            except Exception as exception:
                logger.warning("Error reading frame from server: %s", exception)
                logger.debug(format_exc())
                return False

            if frame is None:
                return False

            kind = frame.get("kind")
            if kind == KIND_RESPONSE:
                self.response.emit(frame)
            elif kind == KIND_EVENT:
                self.event.emit(frame)
            else:
                logger.warning("Unknown frame kind=%r", kind)
        return True

    def _flush_outgoing(self) -> bool:
        while True:
            try:
                item = self._outgoing.get_nowait()
            except Empty:
                return True
            if item is _STOP:
                self._running = False
                return True
            try:
                self._client.send_request(item)
            except Exception as exception:
                logger.warning("Error sending request to server: %s", exception)
                logger.debug(format_exc())
                return False

    def _sleep_reconnect(self) -> None:
        deadline = time.monotonic() + RECONNECT_DELAY_S
        while self._running and time.monotonic() < deadline:
            time.sleep(0.1)
