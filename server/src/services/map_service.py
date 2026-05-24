import json
import secrets
from threading import Lock
from uuid import uuid4

from repositories.component_repository import (
    add_road_segment,
    delete_description as db_delete_description,
    delete_road as db_delete_road,
    delete_structure as db_delete_structure,
    get_cell_details as db_get_cell_details,
    get_inner_edge_cell,
    get_road_by_id,
    list_inner_edges_for_map,
    list_roads_at_cell,
    list_roads_for_map,
    update_inner_edge_cell,
    upsert_description,
    upsert_inner_edge_cell,
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

MAX_MAP_NAME_LENGTH = 64
MAX_MAP_MEMBERS = 128
_AXIAL_DIRECTIONS = (
    (1, 0), (0, 1), (-1, 1),
    (-1, 0), (0, -1), (1, -1),
)

_tile_locks: dict[tuple, Lock] = {}
_tile_locks_lock = Lock()

def _get_tile_lock(map_id: str, q: int, r: int) -> Lock:
    key = (map_id, q, r)
    with _tile_locks_lock:
        if key not in _tile_locks:
            _tile_locks[key] = Lock()
        return _tile_locks[key]

def _invite_code() -> str:
    raw = secrets.token_hex(4)
    return f"{raw[:4]}-{raw[4:8]}"

def _normalize_waypoints(waypoints: list) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for wp in waypoints:
        if not isinstance(wp, (list, tuple)) or len(wp) < 2:
            continue
        coords.append((int(wp[0]), int(wp[1])))
    return coords

def _axial_step_direction(start: tuple[int, int], end: tuple[int, int]) -> int | None:
    dq = end[0] - start[0]
    dr = end[1] - start[1]
    for index, (step_q, step_r) in enumerate(_AXIAL_DIRECTIONS):
        if (dq, dr) == (step_q, step_r):
            return index
    return None

def _segment_key(
    start: tuple[int, int],
    end: tuple[int, int],
) -> tuple[tuple[int, int], tuple[int, int]]:
    return (start, end) if start <= end else (end, start)

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
    members = list_members(map_id)
    if len(members) >= MAX_MAP_MEMBERS:
        return "map_full"
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
    members = list_members(map_id)
    roads_rows = list_roads_for_map(map_id)
    roads = [
        {
            "id": r["id"],
            "waypoints": json.loads(r["waypoints"]),
            "color": r["color"],
        }
        for r in roads_rows
    ]
    inner_edges_rows = list_inner_edges_for_map(map_id)
    inner_edges = [
        {
            "q": row["q"],
            "r": row["r"],
            "edges": row["edges"],
            "color": row["color"],
        }
        for row in inner_edges_rows
    ]
    return {
        "map_id": map_id,
        "name": row["name"],
        "role": role,
        "tiles": tiles,
        "roads": roads,
        "inner_edges": inner_edges,
        "member_count": len(members),
    }

def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return row if isinstance(row, dict) else dict(row)

def get_cell_details(map_id: str, tile_id: str) -> dict | str:
    tile = _row_to_dict(get_tile_by_id(tile_id))
    if tile is None or tile["map_id"] != map_id:
        return "not_found"
    details = db_get_cell_details(tile_id, map_id, tile["q"], tile["r"])
    roads = [_row_to_dict(row) for row in list_roads_at_cell(map_id, tile["q"], tile["r"])]
    author_ids = set()
    for key in ("structure", "description", "inner_edge"):
        component = _row_to_dict(details.get(key))
        if component and component.get("author_id"):
            author_ids.add(component["author_id"])
    for road in roads:
        if road.get("author_id"):
            author_ids.add(road["author_id"])
    usernames = {uid: get_user_by_id(uid)["username"] for uid in author_ids if uid}

    def _resolve(component, extra_fields: list[str]) -> dict | None:
        component = _row_to_dict(component)
        if component is None:
            return None
        return {
            **{k: component[k] for k in extra_fields},
            "author": usernames.get(component.get("author_id"), "unknown"),
            "created_at": component.get("created_at"),
            "updated_at": component.get("updated_at"),
        }

    def _resolve_road(road: dict) -> dict:
        return {
            "id": road["id"],
            "color": road["color"],
            "author": usernames.get(road.get("author_id"), "unknown"),
            "created_at": road.get("created_at"),
            "updated_at": road.get("updated_at"),
        }

    return {
        "tile_id": tile_id,
        "q": tile["q"],
        "r": tile["r"],
        "tile": {
            "created_at": tile.get("created_at"),
            "updated_at": tile.get("updated_at"),
        },
        "structure": _resolve(details["structure"], ["type"]),
        "description": _resolve(details["description"], ["text"]),
        "inner_edge": _resolve(details["inner_edge"], ["edges", "color"]),
        "roads": [_resolve_road(road) for road in roads],
    }

def set_structure(user_id: str, map_id: str, q: int, r: int, structure_type: str) -> dict | str:
    structure_type = structure_type.strip()
    if not structure_type:
        return "missing_fields"
    with _get_tile_lock(map_id, q, r):
        tile_id = get_or_create_tile(map_id, q, r)
        upsert_structure(tile_id, structure_type, user_id)
    return {"tile_id": tile_id, "q": q, "r": r, "type": structure_type}

def add_road(user_id: str, map_id: str, waypoints: list, color: str) -> dict | str:
    color = color.strip()
    if not color or not waypoints or len(waypoints) < 2:
        return "missing_fields"
    coords = _normalize_waypoints(waypoints)
    if len(coords) < 2:
        return "missing_fields"

    segments: list[dict] = []
    seen_segments: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for start, end in zip(coords, coords[1:]):
        if start == end:
            continue
        if _axial_step_direction(start, end) is None:
            return "invalid_path"
        key = _segment_key(start, end)
        if key in seen_segments:
            return "invalid_path"
        seen_segments.add(key)
        road_id, _created = add_road_segment(map_id, start, end, color, user_id)
        segments.append({
            "road_id": road_id,
            "waypoints": [[start[0], start[1]], [end[0], end[1]]],
            "color": color,
        })
    if not segments:
        return "missing_fields"
    return {"segments": segments}

def set_inner_edge(
    user_id: str,
    map_id: str,
    q: int,
    r: int,
    edge_index: int,
    color: str,
) -> dict | str:
    color = color.strip()
    if edge_index < 0 or edge_index > 5 or not color:
        return "missing_fields"
    bit = 1 << edge_index
    with _get_tile_lock(map_id, q, r):
        row = get_inner_edge_cell(map_id, q, r)
        current_edges = int(row["edges"]) if row else 0
        next_edges = current_edges | bit
        upsert_inner_edge_cell(map_id, q, r, next_edges, color, user_id)
    return {
        "cells": [{
            "q": q,
            "r": r,
            "edges": next_edges,
            "color": color,
        }],
    }

def remove_inner_edge(
    user_id: str,
    map_id: str,
    q: int,
    r: int,
    edge_index: int,
) -> dict | str:
    if edge_index < 0 or edge_index > 5:
        return "missing_fields"
    bit = 1 << edge_index
    with _get_tile_lock(map_id, q, r):
        row = get_inner_edge_cell(map_id, q, r)
        if row is None:
            return "not_found"
        next_edges = int(row["edges"]) & ~bit
        color = row["color"]
        update_inner_edge_cell(map_id, q, r, next_edges, color, user_id)
    return {
        "cells": [{
            "q": q,
            "r": r,
            "edges": next_edges,
            "color": color,
        }],
    }

def set_description(user_id: str, map_id: str, q: int, r: int, text: str) -> dict | str:
    text = text.strip()
    if not text:
        return "missing_fields"
    with _get_tile_lock(map_id, q, r):
        tile_id = get_or_create_tile(map_id, q, r)
        upsert_description(tile_id, text, user_id)
    return {"tile_id": tile_id, "q": q, "r": r, "text": text}

def remove_structure(map_id: str, tile_id: str) -> dict | str:
    tile = get_tile_by_id(tile_id)
    if tile is None or tile["map_id"] != map_id:
        return "not_found"
    with _get_tile_lock(map_id, tile["q"], tile["r"]):
        db_delete_structure(tile_id)
    return {"tile_id": tile_id, "q": tile["q"], "r": tile["r"]}

def remove_road(map_id: str, road_id: str) -> dict | str:
    road = get_road_by_id(road_id)
    if road is None or road["map_id"] != map_id:
        return "not_found"
    db_delete_road(road_id)
    return {"road_id": road_id}

def remove_description(map_id: str, tile_id: str) -> dict | str:
    tile = get_tile_by_id(tile_id)
    if tile is None or tile["map_id"] != map_id:
        return "not_found"
    with _get_tile_lock(map_id, tile["q"], tile["r"]):
        db_delete_description(tile_id)
    return {"tile_id": tile_id, "q": tile["q"], "r": tile["r"]}

def delete_map(user_id: str, map_id: str) -> str | None:
    if get_role(user_id, map_id) != "owner":
        return "not_owner"
    members = list_members(map_id)
    if len(members) > 1:
        return "map_has_members"
    db_delete_map(map_id)
    return None
