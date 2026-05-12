from socket import socket

from transport.protocol import recv_request, send_response
from controllers.request_controller import handle_request
from database.connection import close_connection

class Connection:
    def __init__(self, client_socket: socket, client_address: tuple[str, int]) -> None:
        self._client_socket = client_socket
        self._client_address = client_address

    def start(self) -> None:
        print(f"Client {self._client_address[0]}:{self._client_address[1]} connected")
        try:
            while True:
                request = recv_request(self._client_socket)
                if request is None:
                    break
                response = handle_request(request)
                send_response(self._client_socket, response)
        except Exception as exception:
            print(f"Error while handling client {self._client_address[0]}:{self._client_address[1]} request: {exception}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        close_connection()
        if self._client_socket:
            self._client_socket.close()
            self._client_socket = None
        print(f"Client {self._client_address[0]}:{self._client_address[1]} disconnected")