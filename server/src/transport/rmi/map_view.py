import Pyro5.api

from transport.rmi.base import _RemoteBase

@Pyro5.api.expose
class MapView(_RemoteBase):
    def get_map_state(self, token: str, map_id: str) -> dict:
        return self._auth_call("get_map_state", token, {"map_id": map_id})

    def get_tile_details(self, token: str, map_id: str, tile_id: str) -> dict:
        return self._auth_call(
            "get_tile_details", token, {"map_id": map_id, "tile_id": tile_id}
        )
