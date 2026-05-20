from os import getenv
from socket import (
    AF_INET,
    IPPROTO_TCP,
    SOCK_STREAM,
    SOL_SOCKET,
    SO_KEEPALIVE,
    SO_REUSEADDR,
    TCP_KEEPCNT,
    TCP_KEEPIDLE,
    TCP_KEEPINTVL,
    socket,
)
from threading import Thread
from traceback import format_exc

from database.connection import close_pool
from transport.connection import Connection

DEFAULT_SERVER_ADDRESS = "0.0.0.0:5000"

class Server:
    def __init__(self) -> None:
        self._server_socket = None
        self._server_address = _resolve_server_address()

    def start(self) -> None:
        try:
            self._server_socket = socket(AF_INET, SOCK_STREAM)
            self._server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._server_socket.bind(self._server_address)
            self._server_socket.listen()
            print(f"Server started on {self._server_address[0]}:{self._server_address[1]}")
        except Exception as exception:
            print(f"Error on starting server: {exception}")
            print(format_exc())
            self.stop()
            raise
        try:
            while True:
                client_socket, client_address = self._server_socket.accept()
                _configure_keepalive(client_socket)
                client_connection = Connection(client_socket, client_address)
                Thread(target=client_connection.start, daemon=True).start()
        except KeyboardInterrupt:
            print("Server stopped by keyboard interrupt")
        finally:
            self.stop()
    
    def stop(self) -> None:
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
        close_pool()
        print("Server stopped")

def _configure_keepalive(sock: socket) -> None:
    sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 30)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 10)
    sock.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 3)

def _resolve_server_address() -> tuple[str, int]:
    raw = getenv("SERVER_ADDRESS", DEFAULT_SERVER_ADDRESS)
    host, _, port = raw.rpartition(":")
    if not host or not port:
        raise Exception(f"Invalid SERVER_ADDRESS '{raw}', expected 'host:port'")
    return host, int(port)
