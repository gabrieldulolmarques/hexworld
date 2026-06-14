from repositories.path_repository import PathRepository
from repositories.user_map_repository import UserMapRepository
from utils.roles import has_role

_AXIAL_DIRECTIONS = (
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
    (1, -1),
)

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

class PathService:
    def __init__(
        self,
        path_repository: PathRepository,
        user_map_repository: UserMapRepository,
    ) -> None:
        self._path_repository = path_repository
        self._user_map_repository = user_map_repository

    def add_path(
        self, user_id: str, map_id: str, waypoints: list, color: str
    ) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        color = color.strip()
        if not color or not waypoints or len(waypoints) < 2:
            return "missing_fields"
        coords = _normalize_waypoints(waypoints)
        if len(coords) < 2:
            return "missing_fields"

        pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
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
            pairs.append((start, end))
        if not pairs:
            return "missing_fields"
        segments = self._path_repository.add_path_segments(
            map_id, pairs, color, user_id
        )
        return {"segments": segments}

    def remove_path(self, user_id: str, map_id: str, path_id: str) -> dict | str:
        role = self._user_map_repository.get_role(user_id, map_id)
        if not has_role(role, "editor"):
            return "not_editor"
        path = self._path_repository.get_path_by_id(path_id)
        if path is None or path["map_id"] != map_id:
            return "not_found"
        self._path_repository.delete_path(path_id)
        return {"path_id": path_id}
