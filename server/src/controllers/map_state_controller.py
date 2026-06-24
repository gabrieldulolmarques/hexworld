from events.publisher import MapEventPublisher
from services.map_service import MapService
from services.tile_service import TileService
from controllers.responses import error_response, success_response
from events.session import ClientSession

class MapStateController:
    def __init__(
        self,
        map_service: MapService,
        tile_service: TileService,
        publisher: MapEventPublisher,
    ) -> None:
        self._map_service = map_service
        self._tile_service = tile_service
        self._publisher = publisher

    def handle_get_map_state(
        self, request: dict, connection: ClientSession, auth: dict
    ) -> dict:
        map_id = (request.get("data") or {}).get("map_id", "")
        connection.subscribe(map_id)
        entered = connection.enter_presence(map_id)
        result = self._map_service.get_map_state(auth["user_id"], map_id)
        result["online_users"] = self._publisher.get_online_users(map_id)
        if entered:
            self._publisher.presence_changed(map_id, "map_user_online")
        return success_response(request, result)

    def handle_get_tile_details(
        self, request: dict, connection: ClientSession, auth: dict
    ) -> dict:
        data = request.get("data") or {}
        map_id = data.get("map_id", "")
        tile_id = data.get("tile_id", "")
        if not tile_id:
            return error_response(request, "missing_fields")
        result = self._tile_service.get_tile_details(map_id, tile_id)
        if isinstance(result, str):
            return error_response(request, result)
        return success_response(request, result)
