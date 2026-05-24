from traceback import format_exc

from transport.protocol import error_response

from controllers.auth_controller import (
    handle_login,
    handle_logout,
    handle_register,
    handle_validate_session,
)
from controllers.map_controller import (
    handle_add_road,
    handle_close_map,
    handle_create_map,
    handle_delete_map,
    handle_dissociate_map,
    handle_get_cell_details,
    handle_get_map_state,
    handle_get_maps,
    handle_join_map,
    handle_remove_description,
    handle_remove_inner_edge,
    handle_remove_road,
    handle_remove_structure,
    handle_set_description,
    handle_set_inner_edge,
    handle_set_structure,
)

REQUEST_HANDLERS = {
    "register": handle_register,
    "login": handle_login,
    "validate_session": handle_validate_session,
    "logout": handle_logout,
    "create_map": handle_create_map,
    "join_map": handle_join_map,
    "get_maps": handle_get_maps,
    "get_cell_details": handle_get_cell_details,
    "get_map_state": handle_get_map_state,
    "close_map": handle_close_map,
    "dissociate_map": handle_dissociate_map,
    "delete_map": handle_delete_map,
    "set_structure": handle_set_structure,
    "add_road": handle_add_road,
    "set_inner_edge": handle_set_inner_edge,
    "remove_inner_edge": handle_remove_inner_edge,
    "set_description": handle_set_description,
    "remove_structure": handle_remove_structure,
    "remove_road": handle_remove_road,
    "remove_description": handle_remove_description,
}

def handle_request(request: dict, connection) -> dict:
    request_type = request.get("type") or "unknown"
    handler = REQUEST_HANDLERS.get(request_type)
    if handler is None:
        return error_response(request, "unknown_type")
    try:
        return handler(request, connection)
    except Exception as exception:
        print(f"Error handling request {request}: {exception}")
        print(format_exc())
        return error_response(request, "unexpected_error")
