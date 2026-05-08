import socket
import threading

from communication.message import recv_message, send_message
from database.connection import close_connection

class Server:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server = None

    def start(self) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f"Server started on {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                ).start()
        except KeyboardInterrupt:
            print("Server stopped by user")
        except socket.error as exception:
            print(f"Error on starting server: {exception}")
        except Exception as exception:
            print(f"Unexpected error on starting server: {exception}")
        finally:
            self.stop()

    def _handle_client(self, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        print(f"New client connected: {client_address}")
        try:
            while True:
                message = recv_message(client_socket)
                if not message:
                    break
                print(f"Received from {client_address}: {message}")
                response = self._handle_message(message)
                send_message(client_socket, response)   
        except socket.error as exception:
            print(f"Error on handling client {client_address}: {exception}")
        except Exception as exception:
            print(f"Unexpected error on handling client {client_address}: {exception}")
        finally:
            close_connection()
            client_socket.close()
            print(f"Client {client_address} disconnected")

    def _handle_message(self, message: dict) -> dict:
        msg_type = str(message.get("type", "")).lower()

        if msg_type == "ping":
            return {"type": "pong..."}

        return {"success": False, "error": "unknown_message_type"}

    def stop(self) -> None:
        if self.server:
            self.server.close()
        print("Server stopped")
