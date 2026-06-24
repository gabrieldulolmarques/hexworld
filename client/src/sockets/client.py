import logging
from os import getenv
from socket import (
    AF_INET,
    IPPROTO_TCP,
    SO_KEEPALIVE,
    SOCK_STREAM,
    SOL_SOCKET,
    socket,
)
from threading import Lock

from sockets.protocol import recv_response as read_response
from sockets.protocol import send_request

logger = logging.getLogger(__name__)

DEFAULT_SERVER_ADDRESS = "127.0.0.1:5000"
CONNECT_TIMEOUT_SECONDS = 5.0
SERVER_UNREACHABLE_MESSAGE = "Could not reach the server."

class Client:
    def __init__(self, server_address: str | None = None) -> None:
        self._client_id = getenv("CLIENT_ID")
        self._client_socket = None
        self._server_address = (
            _parse_address(server_address)
            if server_address
            else _resolve_server_address()
        )
        self._io_lock = Lock()

    def set_server_address(self, raw: str) -> None:
        new_address = _parse_address(raw)
        with self._io_lock:
            if new_address == self._server_address:
                return
            self._server_address = new_address
            self._disconnect_locked()

    def is_connected(self) -> bool:
        return self._client_socket is not None

    def socket_fileno(self) -> int | None:
        with self._io_lock:
            if self._client_socket is None:
                return None
            return self._client_socket.fileno()

    def ensure_connected(self) -> None:
        with self._io_lock:
            if not self.is_connected():
                self._connect()

    def send_request(self, request: dict) -> None:
        with self._io_lock:
            if not self.is_connected():
                self._connect()
            try:
                send_request(self._client_socket, request)
            except Exception as exception:
                self._disconnect_locked()
                raise Exception(SERVER_UNREACHABLE_MESSAGE) from exception

    def recv_response(self) -> dict | None:
        with self._io_lock:
            if not self.is_connected():
                return None
            try:
                frame = read_response(self._client_socket)
            except Exception as exception:
                self._disconnect_locked()
                raise Exception(SERVER_UNREACHABLE_MESSAGE) from exception
            if frame is None:
                self._disconnect_locked()
            return frame

    def stop(self) -> None:
        with self._io_lock:
            self._disconnect_locked()

    def _disconnect_locked(self) -> None:
        if self._client_socket:
            self._client_socket.close()
            self._client_socket = None
            logger.info(
                "Client %s disconnected from %s:%s (sockets)",
                self._client_id, self._server_address[0], self._server_address[1],
            )

    def _connect(self) -> None:
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT_SECONDS)
            sock.connect(self._server_address)
            sock.settimeout(None)
            _configure_keepalive(sock)
            self._client_socket = sock
            logger.info(
                "Client %s connected to %s:%s (sockets)",
                self._client_id, self._server_address[0], self._server_address[1],
            )
        except Exception as exception:
            self._client_socket = None
            raise Exception(SERVER_UNREACHABLE_MESSAGE) from exception

def _configure_keepalive(sock: socket) -> None:
    import socket as _socket

    sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
    if hasattr(_socket, "TCP_KEEPIDLE"):
        sock.setsockopt(IPPROTO_TCP, _socket.TCP_KEEPIDLE, 30)
    if hasattr(_socket, "TCP_KEEPINTVL"):
        sock.setsockopt(IPPROTO_TCP, _socket.TCP_KEEPINTVL, 10)
    if hasattr(_socket, "TCP_KEEPCNT"):
        sock.setsockopt(IPPROTO_TCP, _socket.TCP_KEEPCNT, 3)

def _resolve_server_address() -> tuple[str, int]:
    return _parse_address(getenv("SERVER_ADDRESS", DEFAULT_SERVER_ADDRESS))

def _parse_address(raw: str) -> tuple[str, int]:
    host, _, port = raw.rpartition(":")
    if not host or not port:
        raise Exception(f"Invalid server address '{raw}', expected 'host:port'")
    return host, int(port)
