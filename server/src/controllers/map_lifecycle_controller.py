from controllers.map_event_publisher import MapEventPublisher
from services.map_service import MapService
from transport.messages import error_response, success_response
from transport.session import ClientSession

class MapLifecycleController:
    def __init__(self, map_service: MapService, publisher: MapEventPublisher) -> None:
        self._map_service = map_service
        self._publisher = publisher

    def handle_create_map(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        name = (request.get("data") or {}).get("name", "")
        result = self._map_service.create_map(auth["user_id"], name)
        if isinstance(result, str):
            return error_response(request, result)
        connection.subscribe(result["id"])
        return success_response(request, {"map": result})

    def handle_join_map(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        code = (request.get("data") or {}).get("code", "")
        result = self._map_service.join_map(auth["user_id"], code)
        if isinstance(result, str):
            return error_response(request, result)
        map_id = result["id"]
        self._publisher.member_joined(map_id, result["member_count"])
        connection.subscribe(map_id)
        return success_response(request, {"map": result})

    def handle_get_maps(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        maps = self._map_service.get_maps(auth["user_id"])
        for m in maps:
            connection.subscribe(m["id"])
        return success_response(request, {"maps": maps})

    def handle_dissociate_map(
        self, request: dict, connection: ClientSession, auth: dict
    ) -> dict:
        map_id = (request.get("data") or {}).get("map_id", "")
        error, result = self._map_service.dissociate_map(auth["user_id"], map_id)
        if error:
            return error_response(request, error)
        was_present = connection.leave_presence(map_id)
        connection.unsubscribe(map_id)
        if was_present:
            self._publisher.presence_changed(map_id, "map_user_offline")
        self._publisher.member_left(map_id, result["member_count"])
        if result["new_owner_id"]:
            self._publisher.ownership_transferred(map_id, result["new_owner_id"])
        return success_response(request, {"map_id": map_id})

    def handle_delete_map(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        map_id = (request.get("data") or {}).get("map_id", "")
        error = self._map_service.delete_map(auth["user_id"], map_id)
        if error:
            return error_response(request, error)
        connection.leave_presence(map_id)
        connection.unsubscribe(map_id)
        return success_response(request, {"map_id": map_id})

    def handle_close_map(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        map_id = (request.get("data") or {}).get("map_id", "")
        if not map_id:
            return error_response(request, "missing_fields")
        if connection.leave_presence(map_id):
            self._publisher.presence_changed(map_id, "map_user_offline")
        return success_response(request, {"map_id": map_id})
