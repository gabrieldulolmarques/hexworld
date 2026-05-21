from controllers.auth_middleware import authenticated, require_role
from services.map_service import (
    create_map,
    delete_map,
    dissociate_map,
    get_map_state,
    get_maps,
    join_map,
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
def handle_get_map_state(request: dict, connection, auth: dict) -> dict:
    map_id = (request.get("data") or {}).get("map_id", "")
    connection.subscribe(map_id)
    result = get_map_state(auth["user_id"], map_id)
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
