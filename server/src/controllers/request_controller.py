import logging

from controllers.auth_controller import AuthController
from controllers.auth_middleware import AuthMiddleware
from controllers.map_edit_controller import MapEditController
from controllers.map_lifecycle_controller import MapLifecycleController
from controllers.map_state_controller import MapStateController
from transport.protocol import error_response

logger = logging.getLogger(__name__)

def _safe_log_request(request: dict) -> str:
    return f"type={request.get('type')!r} request_id={request.get('request_id')!r}"

class RequestController:
    def __init__(
        self,
        map_lifecycle_controller: MapLifecycleController,
        map_state_controller: MapStateController,
        map_edit_controller: MapEditController,
        auth_controller: AuthController,
        auth_middleware: AuthMiddleware,
    ) -> None:
        authenticated = auth_middleware.authenticated
        require_role = auth_middleware.require_role
        self._handlers = {
            "register": auth_controller.handle_register,
            "login": auth_controller.handle_login,
            "validate_session": authenticated(auth_controller.handle_validate_session),
            "logout": authenticated(auth_controller.handle_logout),
            "create_map": authenticated(map_lifecycle_controller.handle_create_map),
            "join_map": authenticated(map_lifecycle_controller.handle_join_map),
            "get_maps": authenticated(map_lifecycle_controller.handle_get_maps),
            "dissociate_map": authenticated(
                map_lifecycle_controller.handle_dissociate_map
            ),
            "delete_map": authenticated(map_lifecycle_controller.handle_delete_map),
            "close_map": authenticated(
                require_role("viewer")(map_lifecycle_controller.handle_close_map)
            ),
            "get_map_state": authenticated(
                require_role("viewer")(map_state_controller.handle_get_map_state)
            ),
            "get_tile_details": authenticated(
                require_role("viewer")(map_state_controller.handle_get_tile_details)
            ),
            "set_terrain": authenticated(
                require_role("editor")(map_edit_controller.handle_set_terrain)
            ),
            "add_path": authenticated(
                require_role("editor")(map_edit_controller.handle_add_path)
            ),
            "set_edge": authenticated(
                require_role("editor")(map_edit_controller.handle_set_edge)
            ),
            "remove_edge": authenticated(
                require_role("editor")(map_edit_controller.handle_remove_edge)
            ),
            "set_description": authenticated(
                require_role("editor")(map_edit_controller.handle_set_description)
            ),
            "remove_terrain": authenticated(
                require_role("editor")(map_edit_controller.handle_remove_terrain)
            ),
            "remove_path": authenticated(
                require_role("editor")(map_edit_controller.handle_remove_path)
            ),
            "remove_description": authenticated(
                require_role("editor")(map_edit_controller.handle_remove_description)
            ),
        }

    def handle_request(self, request: dict, connection) -> dict:
        request_type = request.get("type") or "unknown"
        handler = self._handlers.get(request_type)
        if handler is None:
            return error_response(request, "unknown_type")
        try:
            return handler(request, connection)
        except Exception:
            logger.exception("Error handling request [%s]", _safe_log_request(request))
            return error_response(request, "unexpected_error")
