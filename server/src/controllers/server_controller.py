from socket import socket

from communication.protocol import recv_request, send_response
from controllers.auth_controller import (
    handle_login,
    handle_logout,
    handle_register,
    handle_validate_session,
)
from database.connection import close_connection

def handle_client(client_socket: socket, client_address: tuple[str, int]) -> None:
    print(f"New client connected: {client_address}")
    try:
        while True:
            request = recv_request(client_socket)
            if not request:
                break
            response = handle_request(request)
            send_response(client_socket, response)
    except Exception as exception:
        print(f"Error on handling client {client_address}: {exception}")
    finally:
        close_connection()
        client_socket.close()
        print(f"Client {client_address} disconnected")

def handle_request(request: dict) -> dict:
    match str(request.get("type", "")).lower():
        case "register":
            return handle_register(request)
        case "login":
            return handle_login(request)
        case "logout":
            return handle_logout(request)
        case "validate_session":
            return handle_validate_session(request)
        case _:
            return {"type": str(request.get("type", "")), "status": "error", "code": "unknown_type"}
