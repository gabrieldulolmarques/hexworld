import logging
from collections.abc import Callable
from socket import socket
from threading import Lock

from transport.broadcaster import Broadcaster
from transport.presence import Presence
from transport.session import ClientSession
from transport.sockets.protocol import recv_request, send_response

logger = logging.getLogger(__name__)

BroadcastPresenceFn = Callable[[str, str], None]
RequestHandlerFn = Callable[[dict, ClientSession], dict]

class Connection:  # implements ClientSession
    def __init__(
        self,
        client_socket: socket,
        client_address: tuple[str, int],
        *,
        handle_request: RequestHandlerFn,
        broadcast_presence: BroadcastPresenceFn,
        broadcaster: Broadcaster,
        presence: Presence,
    ) -> None:
        self._client_socket = client_socket
        self._client_address = client_address
        self._handle_request = handle_request
        self._broadcast_presence = broadcast_presence
        self._broadcaster = broadcaster
        self._presence = presence
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
        with self._send_lock:
            if self._client_socket is None:
                return
            send_response(self._client_socket, payload)

    def subscribe(self, map_id: str) -> None:
        self._broadcaster.subscribe(map_id, self)
        self._subscribed_maps.add(map_id)

    def unsubscribe(self, map_id: str) -> None:
        self._broadcaster.unsubscribe(map_id, self)
        self._subscribed_maps.discard(map_id)

    def enter_presence(self, map_id: str) -> bool:
        return self._presence.enter(map_id, self)

    def leave_presence(self, map_id: str) -> bool:
        return self._presence.leave(map_id, self)

    def is_present_in(self, map_id: str) -> bool:
        return self._presence.is_present(map_id, self)

    def start(self) -> None:
        logger.info("Client %s:%s connected", *self._client_address)
        try:
            while True:
                request = recv_request(self._client_socket)
                if request is None:
                    break
                response = self._handle_request(request, self)
                self.send(response)
        except Exception:
            logger.exception(
                "Error handling client %s:%s request", *self._client_address
            )
        finally:
            self.stop()

    def stop(self) -> None:
        presence_maps = self._presence.leave_all(self)
        for map_id in list(self._subscribed_maps):
            self._broadcaster.unsubscribe(map_id, self)
        self._subscribed_maps.clear()
        for map_id in presence_maps:
            self._broadcast_presence(map_id, "map_user_offline")
        with self._send_lock:
            if self._client_socket:
                self._client_socket.close()
                self._client_socket = None
        logger.info("Client %s:%s disconnected", *self._client_address)
