from socket import socket
from threading import Lock
from traceback import format_exc

from controllers.request_controller import handle_request
from transport.broadcaster import broadcaster
from transport.protocol import recv_request, send_response

class Connection:
    def __init__(self, client_socket: socket, client_address: tuple[str, int]) -> None:
        self._client_socket = client_socket
        self._client_address = client_address
        self._send_lock = Lock()
        self._subscribed_maps: set[str] = set()
        self._user_id: str | None = None
        self._username: str | None = None

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def username(self) -> str | None:
        return self._username

    def bind_user(self, user_id: str, username: str) -> None:
        self._user_id = user_id
        self._username = username

    def send(self, payload: dict) -> None:
        """Serialize response/event writes on this socket (response and event must not interleave)."""
        with self._send_lock:
            if self._client_socket is None:
                return
            send_response(self._client_socket, payload)

    def subscribe(self, map_id: str) -> None:
        broadcaster.subscribe(map_id, self)
        self._subscribed_maps.add(map_id)

    def unsubscribe(self, map_id: str) -> None:
        broadcaster.unsubscribe(map_id, self)
        self._subscribed_maps.discard(map_id)

    def start(self) -> None:
        print(f"Client {self._client_address[0]}:{self._client_address[1]} connected")
        try:
            while True:
                request = recv_request(self._client_socket)
                if request is None:
                    break
                response = handle_request(request, self)
                self.send(response)
        except Exception as exception:
            print(f"Error handling client {self._client_address[0]}:{self._client_address[1]} request: {exception}")
            print(format_exc())
        finally:
            self.stop()

    def stop(self) -> None:
        from services.presence_service import broadcast_presence

        for map_id in list(self._subscribed_maps):
            user_id = self._user_id
            is_last = (
                user_id
                and sum(
                    1
                    for c in broadcaster.connections_for(map_id)
                    if c.user_id == user_id
                )
                == 1
            )
            broadcaster.unsubscribe(map_id, self)
            if is_last:
                broadcast_presence(map_id, "map_user_offline")
        self._subscribed_maps.clear()
        with self._send_lock:
            if self._client_socket:
                self._client_socket.close()
                self._client_socket = None
        print(f"Client {self._client_address[0]}:{self._client_address[1]} disconnected")
