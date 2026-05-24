from controllers.auth_middleware import authenticated, require_role
from repositories.tile_repository import serialize_tile
from services.map_service import (
    add_road,
    create_map,
    delete_map,
    dissociate_map,
    get_cell_details,
    get_map_state,
    get_maps,
    join_map,
    remove_description,
    remove_inner_edge,
    remove_road,
    remove_structure,
    set_description,
    set_inner_edge,
    set_structure,
)
from services.presence_service import broadcast_presence, list_online_users
from transport.broadcaster import broadcaster
from transport.protocol import error_response, event, success_response

def _broadcast_tile(map_id: str, event_type: str, q: int, r: int) -> None:
    broadcaster.broadcast(map_id, event(event_type, serialize_tile(map_id, q, r)))

@authenticated
def handle_create_map(request: dict, connection, auth: dict) -> dict:
    name = (request.get("data") or {}).get("name", "")
    result = create_map(auth["user_id"], name)
    if isinstance(result, str):
        return error_response(request, result)
    connection.subscribe(result["id"])
    return success_response(request, {"map": result})

@authenticated
def handle_join_map(request: dict, connection, auth: dict) -> dict:
    code = (request.get("data") or {}).get("code", "")
    result = join_map(auth["user_id"], code)
    if isinstance(result, str):
        return error_response(request, result)
    map_id = result["id"]
    broadcaster.broadcast(
        map_id,
        event("map_member_joined", {"member_count": result["member_count"]}),
    )
    connection.subscribe(map_id)
    return success_response(request, {"map": result})

@authenticated
def handle_get_maps(request: dict, connection, auth: dict) -> dict:
    maps = get_maps(auth["user_id"])
    for m in maps:
        connection.subscribe(m["id"])
    return success_response(request, {"maps": maps})

@authenticated
def handle_dissociate_map(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    was_present = connection.leave_presence(map_id)
    connection.unsubscribe(map_id)
    error, result = dissociate_map(auth["user_id"], map_id)
    if error:
        connection.subscribe(map_id)
        if was_present:
            connection.enter_presence(map_id)
        return error_response(request, error)
    if was_present:
        broadcast_presence(map_id, "map_user_offline")
    broadcaster.broadcast(
        map_id,
        event("map_member_left", {"member_count": result["member_count"]}),
    )
    if result["new_owner_id"]:
        broadcaster.broadcast(
            map_id,
            event("map_ownership_transferred", {"new_owner_id": result["new_owner_id"]}),
        )
    return success_response(request, {"map_id": map_id})

@authenticated
@require_role("viewer")
def handle_get_cell_details(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    tile_id = data.get("tile_id", "")
    if not tile_id:
        return error_response(request, "missing_fields")
    result = get_cell_details(map_id, tile_id)
    if isinstance(result, str):
        return error_response(request, result)
    return success_response(request, result)

@authenticated
@require_role("viewer")
def handle_get_map_state(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    connection.subscribe(map_id)
    entered = connection.enter_presence(map_id)
    result = get_map_state(auth["user_id"], map_id)
    result["online_users"] = list_online_users(map_id)
    if entered:
        broadcast_presence(map_id, "map_user_online")
    return success_response(request, result)

@authenticated
def handle_close_map(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    if not map_id:
        return error_response(request, "missing_fields")
    if connection.leave_presence(map_id):
        broadcast_presence(map_id, "map_user_offline")
    return success_response(request, {"map_id": map_id})

@authenticated
@require_role("editor")
def handle_set_structure(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    q = data.get("q")
    r = data.get("r")
    structure_type = data.get("type", "")
    if q is None or r is None or not structure_type:
        return error_response(request, "missing_fields")
    result = set_structure(auth["user_id"], map_id, int(q), int(r), structure_type)
    if isinstance(result, str):
        return error_response(request, result)
    _broadcast_tile(map_id, "structure_set", result["q"], result["r"])
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_add_road(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    waypoints = data.get("waypoints")
    color = data.get("color", "")
    if not waypoints or not color:
        return error_response(request, "missing_fields")
    result = add_road(auth["user_id"], map_id, waypoints, color)
    if isinstance(result, str):
        return error_response(request, result)
    broadcaster.broadcast(map_id, event("road_added", result))
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_set_inner_edge(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    q = data.get("q")
    r = data.get("r")
    edge_index = data.get("edge_index")
    color = data.get("color", "")
    if q is None or r is None or edge_index is None or not color:
        return error_response(request, "missing_fields")
    result = set_inner_edge(
        auth["user_id"],
        map_id,
        int(q),
        int(r),
        int(edge_index),
        color,
    )
    if isinstance(result, str):
        return error_response(request, result)
    broadcaster.broadcast(map_id, event("inner_edge_changed", result))
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_remove_inner_edge(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    q = data.get("q")
    r = data.get("r")
    edge_index = data.get("edge_index")
    if q is None or r is None or edge_index is None:
        return error_response(request, "missing_fields")
    result = remove_inner_edge(
        auth["user_id"], map_id, int(q), int(r), int(edge_index),
    )
    if isinstance(result, str):
        return error_response(request, result)
    broadcaster.broadcast(map_id, event("inner_edge_changed", result))
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_set_description(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    q = data.get("q")
    r = data.get("r")
    text = data.get("text", "")
    if q is None or r is None or not text:
        return error_response(request, "missing_fields")
    result = set_description(auth["user_id"], map_id, int(q), int(r), text)
    if isinstance(result, str):
        return error_response(request, result)
    _broadcast_tile(map_id, "description_set", result["q"], result["r"])
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_remove_structure(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    tile_id = data.get("tile_id", "")
    if not tile_id:
        return error_response(request, "missing_fields")
    result = remove_structure(map_id, tile_id)
    if isinstance(result, str):
        return error_response(request, result)
    _broadcast_tile(map_id, "structure_removed", result["q"], result["r"])
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_remove_road(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    road_id = data.get("road_id", "")
    if not road_id:
        return error_response(request, "missing_fields")
    result = remove_road(map_id, road_id)
    if isinstance(result, str):
        return error_response(request, result)
    broadcaster.broadcast(
        map_id,
        event("road_removed", {"road_id": result["road_id"]}),
    )
    return success_response(request, result)

@authenticated
@require_role("editor")
def handle_remove_description(request: dict, connection, auth: dict) -> dict:
    data = request.get("data") or {}
    map_id = data.get("map_id", "")
    tile_id = data.get("tile_id", "")
    if not tile_id:
        return error_response(request, "missing_fields")
    result = remove_description(map_id, tile_id)
    if isinstance(result, str):
        return error_response(request, result)
    _broadcast_tile(map_id, "description_removed", result["q"], result["r"])
    return success_response(request, result)

@authenticated
def handle_delete_map(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    was_present = connection.leave_presence(map_id)
    connection.unsubscribe(map_id)
    error = delete_map(auth["user_id"], map_id)
    if error:
        connection.subscribe(map_id)
        if was_present:
            connection.enter_presence(map_id)
        return error_response(request, error)
    return success_response(request, {"map_id": map_id})
