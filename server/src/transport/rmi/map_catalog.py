import Pyro5.api

from transport.rmi.base import _RemoteBase

@Pyro5.api.expose
class MapCatalog(_RemoteBase):
    def create_map(self, token: str, name: str) -> dict:
        return self._auth_call("create_map", token, {"name": name})

    def join_map(self, token: str, code: str) -> dict:
        return self._auth_call("join_map", token, {"code": code})

    def get_maps(self, token: str) -> dict:
        return self._auth_call("get_maps", token, {})

    def dissociate_map(self, token: str, map_id: str) -> dict:
        return self._auth_call("dissociate_map", token, {"map_id": map_id})

    def delete_map(self, token: str, map_id: str) -> dict:
        return self._auth_call("delete_map", token, {"map_id": map_id})

    def close_map(self, token: str, map_id: str) -> dict:
        return self._auth_call("close_map", token, {"map_id": map_id})
