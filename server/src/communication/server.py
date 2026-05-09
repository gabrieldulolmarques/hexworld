from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
from threading import Thread

from controllers.server_controller import handle_client

class Server:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self._socket = None

    def start(self) -> None:
        try:
            self._socket = socket(AF_INET, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.bind((self.host, self.port))
            self._socket.listen()
            print(f"Server started on {self.host}:{self.port}")
        except Exception as exception:
            print(f"Error on starting server: {exception}")
            self.stop()
            return

        try:
            while True:
                client_socket, client_address = self._socket.accept()
                Thread(
                    target=handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                ).start()
        except Exception as exception:
            print(f"Error while running server: {exception}")
        finally:
            self.stop()

    def stop(self) -> None:
        if self._socket:
            self._socket.close()
            self._socket = None
        print("Server stopped")
