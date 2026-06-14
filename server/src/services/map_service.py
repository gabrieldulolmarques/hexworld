import json
import logging
import secrets
from uuid import uuid4

from repositories.edge_repository import EdgeRepository
from repositories.map_repository import MapRepository
from repositories.path_repository import PathRepository
from repositories.tile_repository import TileRepository
from repositories.user_map_repository import UserMapRepository

MAX_MAP_NAME_LENGTH = 64
MAX_MAP_MEMBERS = 128

logger = logging.getLogger(__name__)

def _invite_code() -> str:
    raw = secrets.token_hex(4)
    return f"{raw[:4]}-{raw[4:8]}"

def _map_payload(row, role: str, member_count: int) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "role": role,
        "member_count": member_count,
        "editor_code": row["editor_code"] if role in ("owner", "editor") else None,
        "viewer_code": row["viewer_code"] if role == "owner" else None,
        "created_at": row["created_at"],
    }

class MapService:
    def __init__(
        self,
        map_repository: MapRepository,
        user_map_repository: UserMapRepository,
        tile_repository: TileRepository,
        path_repository: PathRepository,
        edge_repository: EdgeRepository,
    ) -> None:
        self._map_repository = map_repository
        self._user_map_repository = user_map_repository
        self._tile_repository = tile_repository
        self._path_repository = path_repository
        self._edge_repository = edge_repository

    def create_map(self, user_id: str, name: str) -> dict | str:
        name = name.strip()
        if not name:
            return "missing_fields"
        if len(name) > MAX_MAP_NAME_LENGTH:
            return "map_name_too_long"
        map_id = str(uuid4())
        editor_code = _invite_code()
        viewer_code = _invite_code()
        self._map_repository.create_map(map_id, name, editor_code, viewer_code)
        self._user_map_repository.add_user_to_map(user_id, map_id, "owner")
        row = self._map_repository.get_map_by_id(map_id)
        logger.info("Map %s created by user %s", map_id, user_id)
        return _map_payload(row, "owner", 1)

    def join_map(self, user_id: str, code: str) -> dict | str:
        code = code.strip()
        if not code:
            return "missing_fields"
        result = self._map_repository.get_map_by_code(code)
        if result is None:
            return "invalid_code"
        map_id, role = result
        if self._user_map_repository.get_role(user_id, map_id) is not None:
            return "already_member"
        members = self._user_map_repository.list_members(map_id)
        if len(members) >= MAX_MAP_MEMBERS:
            return "map_full"
        self._user_map_repository.add_user_to_map(user_id, map_id, role)
        row = self._map_repository.get_map_by_id(map_id)
        members = self._user_map_repository.list_members(map_id)
        return _map_payload(row, role, len(members))

    def get_maps(self, user_id: str) -> list[dict]:
        rows = self._map_repository.list_maps_for_user(user_id)
        return [_map_payload(row, row["role"], row["member_count"]) for row in rows]

    def dissociate_map(
        self, user_id: str, map_id: str
    ) -> tuple[str, None] | tuple[None, dict]:
        role = self._user_map_repository.get_role(user_id, map_id)
        if role is None:
            return ("not_member", None)
        members = self._user_map_repository.list_members(map_id)
        new_owner_id = None
        if role == "owner":
            others = [m for m in members if m["user_id"] != user_id]
            if not others:
                return ("use_delete", None)
            oldest = min(others, key=lambda m: m["created_at"])
            self._user_map_repository.transfer_ownership(
                map_id, user_id, oldest["user_id"]
            )
            new_owner_id = oldest["user_id"]
        else:
            self._user_map_repository.remove_user_from_map(user_id, map_id)
        remaining = self._user_map_repository.list_members(map_id)
        return (None, {"member_count": len(remaining), "new_owner_id": new_owner_id})

    def get_map_state(self, user_id: str, map_id: str) -> dict:
        row = self._map_repository.get_map_by_id(map_id)
        role = self._user_map_repository.get_role(user_id, map_id)
        tiles = self._tile_repository.list_tiles_with_components(map_id)
        members = self._user_map_repository.list_members(map_id)
        paths_rows = self._path_repository.list_paths_for_map(map_id)
        paths = [
            {
                "id": r["id"],
                "waypoints": json.loads(r["waypoints"]),
                "color": r["color"],
            }
            for r in paths_rows
        ]
        edges_rows = self._edge_repository.list_edges_for_map(map_id)
        edges = [
            {
                "q": r["q"],
                "r": r["r"],
                "edges": r["edges"],
                "color": r["color"],
            }
            for r in edges_rows
        ]
        return {
            "map_id": map_id,
            "name": row["name"],
            "role": role,
            "tiles": tiles,
            "paths": paths,
            "edges": edges,
            "member_count": len(members),
        }

    def delete_map(self, user_id: str, map_id: str) -> str | None:
        if self._user_map_repository.get_role(user_id, map_id) != "owner":
            return "not_owner"
        members = self._user_map_repository.list_members(map_id)
        if len(members) > 1:
            return "map_has_members"
        self._map_repository.delete_map(map_id)
        logger.info("Map %s deleted by user %s", map_id, user_id)
        return None
