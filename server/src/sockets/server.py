import logging
from os import getenv
from socket import (
    AF_INET,
    IPPROTO_TCP,
    SO_KEEPALIVE,
    SO_REUSEADDR,
    SOCK_STREAM,
    SOL_SOCKET,
    TCP_KEEPCNT,
    TCP_KEEPIDLE,
    TCP_KEEPINTVL,
    socket,
)
from threading import Thread

from database.connection import close_pool
from events.broadcaster import Broadcaster
from events.presence import Presence
from sockets.connection import BroadcastPresenceFn, Connection, RequestHandlerFn
from utils.address import parse_address

logger = logging.getLogger(__name__)

DEFAULT_SERVER_ADDRESS = "0.0.0.0:5000"

class Server:
    def __init__(
        self,
        handle_request: RequestHandlerFn,
        broadcast_presence: BroadcastPresenceFn,
        *,
        broadcaster: Broadcaster,
        presence: Presence,
    ) -> None:
        self._server_socket = None
        self._server_address = _resolve_server_address()
        self._handle_request = handle_request
        self._broadcast_presence = broadcast_presence
        self._broadcaster = broadcaster
        self._presence = presence

    def start(self) -> None:
        try:
            self._server_socket = socket(AF_INET, SOCK_STREAM)
            self._server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._server_socket.bind(self._server_address)
            self._server_socket.listen()
            logger.info("Server started on %s:%s", *self._server_address)
        except Exception:
            logger.exception("Error starting server")
            self.stop()
            raise
        try:
            while True:
                client_socket, client_address = self._server_socket.accept()
                _configure_keepalive(client_socket)
                client_connection = Connection(
                    client_socket,
                    client_address,
                    handle_request=self._handle_request,
                    broadcast_presence=self._broadcast_presence,
                    broadcaster=self._broadcaster,
                    presence=self._presence,
                )
                Thread(target=client_connection.start, daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Server stopped by keyboard interrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
        close_pool()
        logger.info("Server stopped")

def _configure_keepalive(sock: socket) -> None:
    sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 30)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 10)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 3)

def _resolve_server_address() -> tuple[str, int]:
    return parse_address(getenv("SERVER_ADDRESS", DEFAULT_SERVER_ADDRESS))
