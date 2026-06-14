import Pyro5.api

from transport.rmi.base import _RemoteBase

@Pyro5.api.expose
class MapEditor(_RemoteBase):
    def set_terrain(
        self, token: str, map_id: str, q: int, r: int, terrain_type: str
    ) -> dict:
        return self._auth_call(
            "set_terrain",
            token,
            {"map_id": map_id, "q": q, "r": r, "type": terrain_type},
        )

    def add_path(self, token: str, map_id: str, waypoints: list, color: str) -> dict:
        return self._auth_call(
            "add_path",
            token,
            {"map_id": map_id, "waypoints": waypoints, "color": color},
        )

    def set_edge(
        self, token: str, map_id: str, q: int, r: int, edge_index: int, color: str
    ) -> dict:
        return self._auth_call(
            "set_edge",
            token,
            {"map_id": map_id, "q": q, "r": r, "edge_index": edge_index, "color": color},
        )

    def remove_edge(
        self, token: str, map_id: str, q: int, r: int, edge_index: int
    ) -> dict:
        return self._auth_call(
            "remove_edge",
            token,
            {"map_id": map_id, "q": q, "r": r, "edge_index": edge_index},
        )

    def set_description(
        self, token: str, map_id: str, q: int, r: int, text: str
    ) -> dict:
        return self._auth_call(
            "set_description",
            token,
            {"map_id": map_id, "q": q, "r": r, "text": text},
        )

    def remove_terrain(self, token: str, map_id: str, tile_id: str) -> dict:
        return self._auth_call(
            "remove_terrain", token, {"map_id": map_id, "tile_id": tile_id}
        )

    def remove_path(self, token: str, map_id: str, path_id: str) -> dict:
        return self._auth_call(
            "remove_path", token, {"map_id": map_id, "path_id": path_id}
        )

    def remove_description(self, token: str, map_id: str, tile_id: str) -> dict:
        return self._auth_call(
            "remove_description", token, {"map_id": map_id, "tile_id": tile_id}
        )
