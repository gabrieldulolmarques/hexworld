from controllers.auth_middleware import authenticated, require_role
from services.map_service import (
    create_map,
    delete_map,
    dissociate_map,
    get_cell_details,
    get_map_state,
    get_maps,
    join_map,
    set_structure,
)
from transport.broadcaster import broadcaster
from transport.protocol import error_response, event, success_response


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
    # Broadcast to existing subscribers before subscribing ourselves so we don't
    # receive our own join event.
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
    connection.unsubscribe(map_id)
    error, result = dissociate_map(auth["user_id"], map_id)
    if error:
        connection.subscribe(map_id)
        return error_response(request, error)
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
    result = get_map_state(auth["user_id"], map_id)
    return success_response(request, result)


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
    return success_response(request, result)


@authenticated
def handle_delete_map(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    connection.unsubscribe(map_id)
    error = delete_map(auth["user_id"], map_id)
    if error:
        connection.subscribe(map_id)
        return error_response(request, error)
    return success_response(request, {"map_id": map_id})
