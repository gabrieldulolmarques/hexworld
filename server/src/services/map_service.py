import secrets
from uuid import uuid4

from repositories.component_repository import (
    add_road as db_add_road,
    get_cell_details as db_get_cell_details,
    upsert_description,
    upsert_structure,
)
from repositories.map_repository import (
    create_map as db_create_map,
    delete_map as db_delete_map,
    get_map_by_code,
    get_map_by_id,
    list_maps_for_user,
)
from repositories.tile_repository import get_or_create_tile, get_tile_by_id, list_tiles_with_components
from repositories.user_map_repository import (
    add_user_to_map,
    get_role,
    list_members,
    remove_user_from_map,
    transfer_ownership,
)
from repositories.user_repository import get_user_by_id

MAX_MAP_NAME_LENGTH = 50


def _invite_code() -> str:
    raw = secrets.token_hex(4)
    return f"{raw[:4]}-{raw[4:8]}"


def _map_payload(row, role: str, members: list) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "role": role,
        "member_count": len(members),
        "editor_code": row["editor_code"] if role in ("owner", "editor") else None,
        "viewer_code": row["viewer_code"] if role == "owner" else None,
        "created_at": row["created_at"],
    }


def create_map(user_id: str, name: str) -> dict | str:
    name = name.strip()
    if not name:
        return "missing_fields"
    if len(name) > MAX_MAP_NAME_LENGTH:
        return "map_name_too_long"
    map_id = str(uuid4())
    editor_code = _invite_code()
    viewer_code = _invite_code()
    db_create_map(map_id, name, editor_code, viewer_code)
    add_user_to_map(user_id, map_id, "owner")
    row = get_map_by_id(map_id)
    return _map_payload(row, "owner", [user_id])


def join_map(user_id: str, code: str) -> dict | str:
    code = code.strip()
    if not code:
        return "missing_fields"
    result = get_map_by_code(code)
    if result is None:
        return "invalid_code"
    map_id, role = result
    if get_role(user_id, map_id) is not None:
        return "already_member"
    add_user_to_map(user_id, map_id, role)
    row = get_map_by_id(map_id)
    members = list_members(map_id)
    return _map_payload(row, role, members)


def get_maps(user_id: str) -> list[dict]:
    rows = list_maps_for_user(user_id)
    result = []
    for row in rows:
        members = list_members(row["id"])
        result.append(_map_payload(row, row["role"], members))
    return result


def dissociate_map(user_id: str, map_id: str) -> tuple[str, None] | tuple[None, dict]:
    role = get_role(user_id, map_id)
    if role is None:
        return ("not_member", None)
    members = list_members(map_id)
    new_owner_id = None
    if role == "owner":
        others = [m for m in members if m["user_id"] != user_id]
        if not others:
            return ("use_delete", None)
        oldest = min(others, key=lambda m: m["created_at"])
        transfer_ownership(map_id, user_id, oldest["user_id"])
        new_owner_id = oldest["user_id"]
    else:
        remove_user_from_map(user_id, map_id)
    remaining = list_members(map_id)
    return (None, {"member_count": len(remaining), "new_owner_id": new_owner_id})


def get_map_state(user_id: str, map_id: str) -> dict:
    row = get_map_by_id(map_id)
    role = get_role(user_id, map_id)
    tiles = list_tiles_with_components(map_id)
    return {"map_id": map_id, "name": row["name"], "role": role, "tiles": tiles}


def get_cell_details(map_id: str, tile_id: str) -> dict | str:
    tile = get_tile_by_id(tile_id)
    if tile is None or tile["map_id"] != map_id:
        return "not_found"
    details = db_get_cell_details(tile_id)
    author_ids = set()
    if details["structure"]:
        author_ids.add(details["structure"]["author_id"])
    if details["description"]:
        author_ids.add(details["description"]["author_id"])
    for road in details["roads"]:
        author_ids.add(road["author_id"])
    usernames = {uid: get_user_by_id(uid)["username"] for uid in author_ids}
    def _resolve(component: dict | None, extra_fields: list[str]) -> dict | None:
        if component is None:
            return None
        return {
            **{k: component[k] for k in extra_fields},
            "author": usernames.get(component["author_id"], "unknown"),
            "created_at": component["created_at"],
        }
    return {
        "tile_id": tile_id,
        "q": tile["q"],
        "r": tile["r"],
        "structure": _resolve(details["structure"], ["type"]),
        "description": _resolve(details["description"], ["text"]),
        "roads": [_resolve(road, ["id", "color"]) for road in details["roads"]],
    }


def set_structure(user_id: str, map_id: str, q: int, r: int, structure_type: str) -> dict | str:
    structure_type = structure_type.strip()
    if not structure_type:
        return "missing_fields"
    tile_id = get_or_create_tile(map_id, q, r)
    upsert_structure(tile_id, structure_type, user_id)
    return {"tile_id": tile_id, "q": q, "r": r, "type": structure_type}


def add_road(user_id: str, map_id: str, q: int, r: int, color: str) -> dict | str:
    color = color.strip()
    if not color:
        return "missing_fields"
    tile_id = get_or_create_tile(map_id, q, r)
    road_id = db_add_road(tile_id, color, user_id)
    return {"tile_id": tile_id, "q": q, "r": r, "road_id": road_id, "color": color}


def set_description(user_id: str, map_id: str, q: int, r: int, text: str) -> dict | str:
    text = text.strip()
    if not text:
        return "missing_fields"
    tile_id = get_or_create_tile(map_id, q, r)
    upsert_description(tile_id, text, user_id)
    return {"tile_id": tile_id, "q": q, "r": r, "text": text}


def delete_map(user_id: str, map_id: str) -> str | None:
    if get_role(user_id, map_id) != "owner":
        return "not_owner"
    members = list_members(map_id)
    if len(members) > 1:
        return "map_has_members"
    db_delete_map(map_id)
    return None
