import logging

from repositories.description_repository import DescriptionRepository
from repositories.edge_repository import EdgeRepository
from repositories.path_repository import PathRepository
from repositories.terrain_repository import TerrainRepository
from repositories.tile_repository import TileRepository
from repositories.user_map_repository import UserMapRepository
from repositories.user_repository import UserRepository
from services._tile_lock import get_tile_lock
from utils.roles import has_role

logger = logging.getLogger(__name__)

def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return row if isinstance(row, dict) else dict(row)

class TileService:
    def __init__(
        self,
        tile_repository: TileRepository,
        terrain_repository: TerrainRepository,
        description_repository: DescriptionRepository,
        edge_repository: EdgeRepository,
        path_repository: PathRepository,
        user_repository: UserRepository,
        user_map_repository: UserMapRepository,
    ) -> None:
        self._tile_repository = tile_repository
        self._terrain_repository = terrain_repository
        self._description_repository = description_repository
        self._edge_repository = edge_repository
        self._path_repository = path_repository
        self._user_repository = user_repository
        self._user_map_repository = user_map_repository

    def get_tile_details(self, map_id: str, tile_id: str) -> dict | str:
        tile = _row_to_dict(self._tile_repository.get_tile_by_id(tile_id))
        if tile is None or tile["map_id"] != map_id:
            return "not_found"
        q, r = tile["q"], tile["r"]
        terrain = _row_to_dict(self._terrain_repository.get_terrain(tile_id))
        description = _row_to_dict(
            self._description_repository.get_description(tile_id)
        )
        edge = _row_to_dict(self._edge_repository.get_edge_tile(map_id, q, r))
        paths = [
            _row_to_dict(row)
            for row in self._path_repository.list_paths_at_tile(map_id, q, r)
        ]
        author_ids = set()
        for component in (terrain, description, edge):
            if component and component.get("author_id"):
                author_ids.add(component["author_id"])
        for path in paths:
            if path.get("author_id"):
                author_ids.add(path["author_id"])
        usernames = self._user_repository.get_users_by_ids(list(author_ids))

        def _resolve(component, extra_fields: list[str]) -> dict | None:
            if component is None:
                return None
            return {
                **{k: component[k] for k in extra_fields},
                "author": usernames.get(component.get("author_id"), "unknown"),
                "created_at": component.get("created_at"),
                "updated_at": component.get("updated_at"),
            }

        def _resolve_road(path: dict) -> dict:
            return {
                "id": path["id"],
                "color": path["color"],
                "author": usernames.get(path.get("author_id"), "unknown"),
                "created_at": path.get("created_at"),
                "updated_at": path.get("updated_at"),
            }

        return {
            "tile_id": tile_id,
            "q": q,
            "r": r,
            "tile": {
                "created_at": tile.get("created_at"),
                "updated_at": tile.get("updated_at"),
            },
            "terrain": _resolve(terrain, ["type"]),
            "description": _resolve(description, ["text"]),
            "edge": _resolve(edge, ["edges", "color"]),
            "paths": [_resolve_road(path) for path in paths],
        }

    def serialize_tile(self, map_id: str, q: int, r: int) -> dict:
        tile = self._tile_repository.get_tile_at(map_id, q, r)
        if tile is None:
            return {"q": q, "r": r}
        tile_id = tile["id"]
        terrain = self._terrain_repository.get_terrain(tile_id)
        description = self._description_repository.get_description(tile_id)
        payload: dict = {"q": q, "r": r, "tile_id": tile_id}
        if terrain:
            payload["terrain"] = dict(terrain)
        if description:
            payload["description"] = dict(description)
        return payload

    def set_terrain(
        self, user_id: str, map_id: str, q: int, r: int, terrain_type: str
    ) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        terrain_type = terrain_type.strip()
        if not terrain_type:
            return "missing_fields"
        with get_tile_lock(map_id, q, r):
            tile_id = self._tile_repository.get_or_create_tile(map_id, q, r)
            self._terrain_repository.upsert_terrain(tile_id, terrain_type, user_id)
            self._tile_repository.touch_tile(tile_id)
        logger.debug("Terrain %r set at (%s, %s) on map %s", terrain_type, q, r, map_id)
        return {"tile_id": tile_id, "q": q, "r": r, "type": terrain_type}

    def set_description(
        self, user_id: str, map_id: str, q: int, r: int, text: str
    ) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        text = text.strip()
        if not text:
            return "missing_fields"
        with get_tile_lock(map_id, q, r):
            tile_id = self._tile_repository.get_or_create_tile(map_id, q, r)
            self._description_repository.upsert_description(tile_id, text, user_id)
            self._tile_repository.touch_tile(tile_id)
        return {"tile_id": tile_id, "q": q, "r": r, "text": text}

    def remove_terrain(self, user_id: str, map_id: str, tile_id: str) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        tile = self._tile_repository.get_tile_by_id(tile_id)
        if tile is None or tile["map_id"] != map_id:
            return "not_found"
        with get_tile_lock(map_id, tile["q"], tile["r"]):
            self._terrain_repository.delete_terrain(tile_id)
            self._tile_repository.touch_tile(tile_id)
        return {"tile_id": tile_id, "q": tile["q"], "r": tile["r"]}

    def remove_description(self, user_id: str, map_id: str, tile_id: str) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        tile = self._tile_repository.get_tile_by_id(tile_id)
        if tile is None or tile["map_id"] != map_id:
            return "not_found"
        with get_tile_lock(map_id, tile["q"], tile["r"]):
            self._description_repository.delete_description(tile_id)
            self._tile_repository.touch_tile(tile_id)
        return {"tile_id": tile_id, "q": tile["q"], "r": tile["r"]}
