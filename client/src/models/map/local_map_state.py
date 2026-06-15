from __future__ import annotations

from models.geometry import Coord
from models.path_constants import DEFAULT_PATH_COLOR

class LocalMapState:
    def __init__(self) -> None:
        self.tiles: dict[Coord, dict] = {}
        self.paths: list[dict] = []
        self.paths_by_coord: dict[Coord, list[str]] = {}
        self.paths_by_id: dict[str, dict] = {}
        self.edges: dict[Coord, dict] = {}

    def clear(self) -> None:
        self.tiles.clear()
        self.paths.clear()
        self.paths_by_coord.clear()
        self.paths_by_id.clear()
        self.edges.clear()

    def set_tiles(self, tiles: dict[Coord, dict]) -> None:
        self.tiles = dict(tiles)

    def apply_tile(self, q: int, r: int, data: dict) -> None:
        self.tiles[(q, r)] = data

    def remove_tile(self, q: int, r: int) -> None:
        self.tiles.pop((q, r), None)

    def tile_at(self, q: int, r: int) -> dict | None:
        return self.tiles.get((q, r))

    def terrain_type_at(self, q: int, r: int) -> str | None:
        tile = self.tile_at(q, r) or {}
        terrain = tile.get("terrain") or {}
        return terrain.get("type") or None

    def description_text(self, q: int, r: int) -> str:
        tile = self.tiles.get((q, r), {})
        desc = tile.get("description") or {}
        return desc.get("text", "")

    def set_paths(self, paths: list[dict]) -> None:
        self.paths = list(paths)
        self._rebuild_path_indexes()

    def apply_path(self, path_id: str, waypoints: list, color: str) -> None:
        self.paths = [r for r in self.paths if r.get("id") != path_id]
        self.paths.append({"id": path_id, "waypoints": waypoints, "color": color})
        self._rebuild_path_indexes()

    def remove_path_by_id(self, path_id: str) -> None:
        self.paths = [r for r in self.paths if r.get("id") != path_id]
        self._rebuild_path_indexes()

    def path_segments_at(self, q: int, r: int) -> list[dict]:
        coord = (q, r)
        found: list[dict] = []
        for path in self.paths:
            path_id = path.get("id", "")
            color = path.get("color", DEFAULT_PATH_COLOR)
            for segment_id, start, end in self._path_segments(path):
                if start == coord or end == coord:
                    found.append(
                        {
                            "path_id": segment_id or path_id,
                            "color": color,
                            "start": start,
                            "end": end,
                        }
                    )
        return found

    def path_by_id(self, path_id: str) -> dict | None:
        return self.paths_by_id.get(path_id)

    def path_ids(self) -> set[str]:
        return set(self.paths_by_id.keys())

    def path_segments_by_color(self) -> dict[str, list[tuple[Coord, Coord]]]:
        by_color: dict[str, list[tuple[Coord, Coord]]] = {}
        for path in self.paths:
            color = path.get("color", DEFAULT_PATH_COLOR)
            for _path_id, start, end in self._path_segments(path):
                by_color.setdefault(color, []).append((start, end))
        return by_color

    def path_segments_for_id(self, path_id: str) -> list[tuple[Coord, Coord]]:
        segments: list[tuple[Coord, Coord]] = []
        for path in self.paths:
            for segment_id, start, end in self._path_segments(path):
                if segment_id == path_id:
                    segments.append((start, end))
        return segments

    def set_edges(self, tiles: list[dict]) -> None:
        self.edges = {}
        for tile in tiles:
            q, r = tile.get("q"), tile.get("r")
            edges = int(tile.get("edges", 0) or 0)
            if q is None or r is None or edges <= 0:
                continue
            self.edges[(int(q), int(r))] = {
                "edges": edges & 0b111111,
                "color": tile.get("color", DEFAULT_PATH_COLOR),
            }

    def apply_edge_tile(self, tile: dict) -> None:
        q, r = tile.get("q"), tile.get("r")
        if q is None or r is None:
            return
        coord = (int(q), int(r))
        edges = int(tile.get("edges", 0) or 0) & 0b111111
        if edges:
            self.edges[coord] = {
                "edges": edges,
                "color": tile.get("color", DEFAULT_PATH_COLOR),
            }
        else:
            self.edges.pop(coord, None)

    def edge_tile(self, q: int, r: int) -> dict | None:
        tile = self.edges.get((q, r))
        return dict(tile) if tile else None

    def edge_snapshot(self, q: int, r: int) -> dict | None:
        tile = self.edge_tile(q, r)
        if not tile:
            return None
        edges = int(tile.get("edges", 0) or 0) & 0b111111
        if not edges:
            return None
        return {"edges": edges, "color": tile.get("color", DEFAULT_PATH_COLOR)}

    def export_coords(self) -> set[Coord]:
        coords: set[Coord] = set(self.tiles)
        coords.update(self.edges)
        for path in self.paths:
            coords.update(self._path_waypoints(path))
        return coords

    def _rebuild_path_indexes(self) -> None:
        self.paths_by_coord = {}
        self.paths_by_id = {}
        for path in self.paths:
            path_id = path.get("id", "")
            if path_id:
                self.paths_by_id[path_id] = path
            for waypoint in path.get("waypoints", []):
                coord = (int(waypoint[0]), int(waypoint[1]))
                if coord not in self.paths_by_coord:
                    self.paths_by_coord[coord] = []
                if path_id and path_id not in self.paths_by_coord[coord]:
                    self.paths_by_coord[coord].append(path_id)

    @staticmethod
    def _path_segments(path: dict) -> list[tuple[str, Coord, Coord]]:
        path_id = path.get("id", "")
        return [
            (path_id, start, end)
            for start, end in LocalMapState._segments_from_waypoints(
                LocalMapState._path_waypoints(path),
            )
        ]

    @staticmethod
    def _segments_from_waypoints(waypoints: list[Coord]) -> list[tuple[Coord, Coord]]:
        return [
            (start, end) for start, end in zip(waypoints, waypoints[1:]) if start != end
        ]

    @staticmethod
    def _path_waypoints(path: dict) -> list[Coord]:
        return [(int(waypoint[0]), int(waypoint[1])) for waypoint in path.get("waypoints", [])]
