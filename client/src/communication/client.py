from os import getenv
from socket import AF_INET, SOCK_STREAM, socket

class Client:
    def __init__(self):
        self.host = getenv("SERVER_HOST", "127.0.0.1")
        self.port = int(getenv("SERVER_PORT", "5000"))
        self.client_id = getenv("CLIENT_ID")
        self._socket = None
    
    def start(self) -> None:
        try:
            self._socket = socket(AF_INET, SOCK_STREAM)
            self._socket.connect((self.host, self.port))
            print(f"Client {self.client_id} started and connected to {self.host}:{self.port}")
        except Exception as exception:
            print(f"Error on starting client {self.client_id} and connecting to {self.host}:{self.port}: {exception}")
            self.stop()
            raise

    def stop(self) -> None:
        if self._socket:
            self._socket.close()
            self._socket = None
        print(f"Client {self.client_id} stopped")
