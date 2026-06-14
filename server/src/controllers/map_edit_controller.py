from controllers.map_event_publisher import MapEventPublisher
from services.edge_service import EdgeService
from services.path_service import PathService
from services.tile_service import TileService
from transport.messages import error_response, success_response

class MapEditController:
    def __init__(
        self,
        tile_service: TileService,
        path_service: PathService,
        edge_service: EdgeService,
        publisher: MapEventPublisher,
    ) -> None:
        self._tile_service = tile_service
        self._path_service = path_service
        self._edge_service = edge_service
        self._publisher = publisher

    def _broadcast_tile(self, map_id: str, event_type: str, q: int, r: int) -> None:
        self._publisher.tile_changed(
            map_id, event_type, self._tile_service.serialize_tile(map_id, q, r)
        )

    def handle_set_terrain(self, request: dict, connection: object, auth: dict) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        q = data.get("q")
        r = data.get("r")
        terrain_type = data.get("type", "")
        if q is None or r is None or not terrain_type:
            return error_response(request, "missing_fields")
        result = self._tile_service.set_terrain(
            auth["user_id"], map_id, int(q), int(r), terrain_type
        )
        if isinstance(result, str):
            return error_response(request, result)
        self._broadcast_tile(map_id, "terrain_set", result["q"], result["r"])
        return success_response(request, result)

    def handle_add_path(self, request: dict, connection: object, auth: dict) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        waypoints = data.get("waypoints")
        color = data.get("color", "")
        if not waypoints or not color:
            return error_response(request, "missing_fields")
        result = self._path_service.add_path(auth["user_id"], map_id, waypoints, color)
        if isinstance(result, str):
            return error_response(request, result)
        self._publisher.path_added(map_id, result)
        return success_response(request, result)

    def handle_set_edge(self, request: dict, connection: object, auth: dict) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        q = data.get("q")
        r = data.get("r")
        edge_index = data.get("edge_index")
        color = data.get("color", "")
        if q is None or r is None or edge_index is None or not color:
            return error_response(request, "missing_fields")
        result = self._edge_service.set_edge(
            auth["user_id"], map_id, int(q), int(r), int(edge_index), color
        )
        if isinstance(result, str):
            return error_response(request, result)
        self._publisher.edge_changed(map_id, result)
        return success_response(request, result)

    def handle_remove_edge(self, request: dict, connection: object, auth: dict) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        q = data.get("q")
        r = data.get("r")
        edge_index = data.get("edge_index")
        if q is None or r is None or edge_index is None:
            return error_response(request, "missing_fields")
        result = self._edge_service.remove_edge(
            auth["user_id"], map_id, int(q), int(r), int(edge_index)
        )
        if isinstance(result, str):
            return error_response(request, result)
        self._publisher.edge_changed(map_id, result)
        return success_response(request, result)

    def handle_set_description(
        self, request: dict, connection: object, auth: dict
    ) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        q = data.get("q")
        r = data.get("r")
        text = data.get("text", "")
        if q is None or r is None or not text:
            return error_response(request, "missing_fields")
        result = self._tile_service.set_description(
            auth["user_id"], map_id, int(q), int(r), text
        )
        if isinstance(result, str):
            return error_response(request, result)
        self._broadcast_tile(map_id, "description_set", result["q"], result["r"])
        return success_response(request, result)

    def handle_remove_terrain(
        self, request: dict, connection: object, auth: dict
    ) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        tile_id = data.get("tile_id", "")
        if not tile_id:
            return error_response(request, "missing_fields")
        result = self._tile_service.remove_terrain(auth["user_id"], map_id, tile_id)
        if isinstance(result, str):
            return error_response(request, result)
        self._broadcast_tile(map_id, "terrain_removed", result["q"], result["r"])
        return success_response(request, result)

    def handle_remove_path(self, request: dict, connection: object, auth: dict) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        path_id = data.get("path_id", "")
        if not path_id:
            return error_response(request, "missing_fields")
        result = self._path_service.remove_path(auth["user_id"], map_id, path_id)
        if isinstance(result, str):
            return error_response(request, result)
        self._publisher.path_removed(map_id, result["path_id"])
        return success_response(request, result)

    def handle_remove_description(
        self, request: dict, connection: object, auth: dict
    ) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        tile_id = data.get("tile_id", "")
        if not tile_id:
            return error_response(request, "missing_fields")
        result = self._tile_service.remove_description(auth["user_id"], map_id, tile_id)
        if isinstance(result, str):
            return error_response(request, result)
        self._broadcast_tile(map_id, "description_removed", result["q"], result["r"])
        return success_response(request, result)
