from collections.abc import Callable
from uuid import uuid4

import Pyro5.api
from Pyro5.server import behavior

from transport.broadcaster import Broadcaster
from transport.presence import Presence
from transport.rmi.client_session import BroadcastPresenceFn, RmiClientSession
from transport.session import ClientSession

RequestHandlerFn = Callable[[dict, ClientSession], dict]

def create_hexworld_api(
    handle_request: RequestHandlerFn,
    broadcast_presence: BroadcastPresenceFn,
    broadcaster: Broadcaster,
    presence: Presence,
) -> type:
    @behavior(instance_mode="session")
    class HexWorldApi:
        def __init__(self) -> None:
            self._session = RmiClientSession(broadcaster, presence, broadcast_presence)

        def _pyroDisconnect(self) -> None:
            self._session.cleanup()

        @Pyro5.api.expose
        def register_event_callback(self, callback_uri: str) -> None:
            self._session.set_event_callback(callback_uri)

        def _dispatch(self, request_type: str, data: dict | None) -> dict:
            request = {
                "type": request_type,
                "request_id": str(uuid4()),
                "data": data or {},
            }
            return handle_request(request, self._session)

        @Pyro5.api.expose
        def register(self, data: dict) -> dict:
            return self._dispatch("register", data)

        @Pyro5.api.expose
        def login(self, data: dict) -> dict:
            return self._dispatch("login", data)

        @Pyro5.api.expose
        def validate_session(self, data: dict) -> dict:
            return self._dispatch("validate_session", data)

        @Pyro5.api.expose
        def logout(self, data: dict) -> dict:
            return self._dispatch("logout", data)

        @Pyro5.api.expose
        def create_map(self, data: dict) -> dict:
            return self._dispatch("create_map", data)

        @Pyro5.api.expose
        def join_map(self, data: dict) -> dict:
            return self._dispatch("join_map", data)

        @Pyro5.api.expose
        def get_maps(self, data: dict) -> dict:
            return self._dispatch("get_maps", data)

        @Pyro5.api.expose
        def dissociate_map(self, data: dict) -> dict:
            return self._dispatch("dissociate_map", data)

        @Pyro5.api.expose
        def delete_map(self, data: dict) -> dict:
            return self._dispatch("delete_map", data)

        @Pyro5.api.expose
        def close_map(self, data: dict) -> dict:
            return self._dispatch("close_map", data)

        @Pyro5.api.expose
        def get_map_state(self, data: dict) -> dict:
            return self._dispatch("get_map_state", data)

        @Pyro5.api.expose
        def get_tile_details(self, data: dict) -> dict:
            return self._dispatch("get_tile_details", data)

        @Pyro5.api.expose
        def set_terrain(self, data: dict) -> dict:
            return self._dispatch("set_terrain", data)

        @Pyro5.api.expose
        def add_path(self, data: dict) -> dict:
            return self._dispatch("add_path", data)

        @Pyro5.api.expose
        def set_edge(self, data: dict) -> dict:
            return self._dispatch("set_edge", data)

        @Pyro5.api.expose
        def remove_edge(self, data: dict) -> dict:
            return self._dispatch("remove_edge", data)

        @Pyro5.api.expose
        def set_description(self, data: dict) -> dict:
            return self._dispatch("set_description", data)

        @Pyro5.api.expose
        def remove_terrain(self, data: dict) -> dict:
            return self._dispatch("remove_terrain", data)

        @Pyro5.api.expose
        def remove_path(self, data: dict) -> dict:
            return self._dispatch("remove_path", data)

        @Pyro5.api.expose
        def remove_description(self, data: dict) -> dict:
            return self._dispatch("remove_description", data)

    HexWorldApi.__name__ = "HexWorldApi"
    return HexWorldApi
