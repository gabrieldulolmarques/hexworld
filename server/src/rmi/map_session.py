import logging

import Pyro5.api

from events.publisher import MapEventPublisher
from services.edge_service import EdgeService
from services.map_service import MapService
from services.path_service import PathService
from services.tile_service import TileService
from rmi.errors import HexworldError

logger = logging.getLogger(__name__)

@Pyro5.api.expose
class MapSession:
    """A single map opened by a single client. Created by Session.open_map."""

    def __init__(
        self,
        owner,
        map_id: str,
        map_service: MapService,
        tile_service: TileService,
        path_service: PathService,
        edge_service: EdgeService,
        publisher: MapEventPublisher,
    ) -> None:
        self._owner = owner
        self._map_id = map_id
        self._map_service = map_service
        self._tile_service = tile_service
        self._path_service = path_service
        self._edge_service = edge_service
        self._publisher = publisher

    @property
    def map_id(self) -> str:
        return self._map_id

    def _enter(self) -> None:
        self._owner.subscribe(self._map_id)
        if self._owner.enter_presence(self._map_id):
            self._publisher.presence_changed(self._map_id, "map_user_online")

    def get_state(self) -> dict:
        result = self._map_service.get_map_state(self._owner.user_id, self._map_id)
        result["online_users"] = self._publisher.get_online_users(self._map_id)
        return result

    def get_tile_details(self, tile_id: str) -> dict:
        result = self._tile_service.get_tile_details(self._map_id, tile_id)
        return _unwrap(result)

    def set_terrain(self, q: int, r: int, terrain_type: str) -> dict:
        result = self._tile_service.set_terrain(
            self._owner.user_id, self._map_id, int(q), int(r), terrain_type
        )
        result = _unwrap(result)
        self._broadcast_tile("terrain_set", result["q"], result["r"])
        return result

    def set_description(self, q: int, r: int, text: str) -> dict:
        result = self._tile_service.set_description(
            self._owner.user_id, self._map_id, int(q), int(r), text
        )
        result = _unwrap(result)
        self._broadcast_tile("description_set", result["q"], result["r"])
        return result

    def remove_terrain(self, tile_id: str) -> dict:
        result = _unwrap(
            self._tile_service.remove_terrain(self._owner.user_id, self._map_id, tile_id)
        )
        self._broadcast_tile("terrain_removed", result["q"], result["r"])
        return result

    def remove_description(self, tile_id: str) -> dict:
        result = _unwrap(
            self._tile_service.remove_description(
                self._owner.user_id, self._map_id, tile_id
            )
        )
        self._broadcast_tile("description_removed", result["q"], result["r"])
        return result

    def add_path(self, waypoints: list, color: str) -> dict:
        result = _unwrap(
            self._path_service.add_path(
                self._owner.user_id, self._map_id, waypoints, color
            )
        )
        self._publisher.path_added(self._map_id, result)
        return result

    def remove_path(self, path_id: str) -> dict:
        result = _unwrap(
            self._path_service.remove_path(self._owner.user_id, self._map_id, path_id)
        )
        self._publisher.path_removed(self._map_id, result["path_id"])
        return result

    def set_edge(self, q: int, r: int, edge_index: int, color: str) -> dict:
        result = _unwrap(
            self._edge_service.set_edge(
                self._owner.user_id, self._map_id, int(q), int(r), int(edge_index), color
            )
        )
        self._publisher.edge_changed(self._map_id, result)
        return result

    def remove_edge(self, q: int, r: int, edge_index: int) -> dict:
        result = _unwrap(
            self._edge_service.remove_edge(
                self._owner.user_id, self._map_id, int(q), int(r), int(edge_index)
            )
        )
        self._publisher.edge_changed(self._map_id, result)
        return result

    def close(self) -> None:
        self._owner.close_map(self._map_id)

    def _broadcast_tile(self, event_type: str, q: int, r: int) -> None:
        self._publisher.tile_changed(
            self._map_id,
            event_type,
            self._tile_service.serialize_tile(self._map_id, q, r),
        )

def _unwrap(result: dict | str) -> dict:
    if isinstance(result, str):
        raise HexworldError(result)
    return result
