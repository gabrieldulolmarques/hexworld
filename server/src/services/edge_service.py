from repositories.edge_repository import EdgeRepository
from repositories.user_map_repository import UserMapRepository
from services._tile_lock import get_tile_lock
from utils.roles import has_role

class EdgeService:
    def __init__(
        self,
        edge_repository: EdgeRepository,
        user_map_repository: UserMapRepository,
    ) -> None:
        self._edge_repository = edge_repository
        self._user_map_repository = user_map_repository

    def set_edge(
        self,
        user_id: str,
        map_id: str,
        q: int,
        r: int,
        edge_index: int,
        color: str,
    ) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        color = color.strip()
        if edge_index < 0 or edge_index > 5 or not color:
            return "missing_fields"
        bit = 1 << edge_index
        with get_tile_lock(map_id, q, r):
            row = self._edge_repository.get_edge_tile(map_id, q, r)
            current_edges = int(row["edges"]) if row else 0
            next_edges = current_edges | bit
            self._edge_repository.upsert_edge_tile(
                map_id, q, r, next_edges, color, user_id
            )
        return {
            "tiles": [
                {
                    "q": q,
                    "r": r,
                    "edges": next_edges,
                    "color": color,
                }
            ],
        }

    def remove_edge(
        self,
        user_id: str,
        map_id: str,
        q: int,
        r: int,
        edge_index: int,
    ) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        if edge_index < 0 or edge_index > 5:
            return "missing_fields"
        bit = 1 << edge_index
        with get_tile_lock(map_id, q, r):
            row = self._edge_repository.get_edge_tile(map_id, q, r)
            if row is None:
                return "not_found"
            next_edges = int(row["edges"]) & ~bit
            color = row["color"]
            if next_edges:
                self._edge_repository.upsert_edge_tile(
                    map_id, q, r, next_edges, color, user_id
                )
            else:
                self._edge_repository.delete_edge_tile(map_id, q, r)
        return {
            "tiles": [
                {
                    "q": q,
                    "r": r,
                    "edges": next_edges,
                    "color": color,
                }
            ],
        }
