from models.geometry import (
    Coord,
    distance_to_polyline,
    hex_to_pixel,
    hex_vertices,
    pixel_to_hex,
)
from views.map.canvas.layers.description_layer import description_badge_center
from views.map.canvas.layers.edge_layer import edge_size
from views.map.canvas.layers.path_layer import path_segments

class PickHelper:
    def __init__(self, canvas) -> None:
        self._canvas = canvas

    def canvas_to_hex(self, cx: float, cy: float) -> Coord:
        ox, oy = self._canvas._origin()
        return pixel_to_hex(cx - ox, cy - oy, self._canvas._hex_size)

    def pick_hex(self, cx: float, cy: float) -> Coord | None:
        q, r = self.canvas_to_hex(cx, cy)
        loose = self._canvas._pick_any_hex or self._canvas._path_mode
        if not loose:
            in_tile = (q, r) in self._canvas._state.tiles
            in_path = self._canvas._erase_mode and (q, r) in self._canvas._state.paths_by_coord
            if not in_tile and not in_path:
                return None
            ox, oy = self._canvas._origin()
            hpx, hpy = hex_to_pixel(q, r, self._canvas._hex_size)
            dist_sq = (cx - ox - hpx) ** 2 + (cy - oy - hpy) ** 2
            if dist_sq > (self._canvas._hex_size * 0.92) ** 2:
                return None
        return (q, r)

    def pick_edge(self, cx: float, cy: float) -> tuple[Coord, int] | None:
        q, r = self.canvas_to_hex(cx, cy)
        ox, oy = self._canvas._origin()
        px, py = hex_to_pixel(q, r, self._canvas._hex_size)
        vertices = hex_vertices(ox + px, oy + py, edge_size(self._canvas._hex_size))
        tolerance = max(8.0, self._canvas._hex_size * 0.18)
        best: tuple[int, float] | None = None
        for edge_index in range(6):
            p1 = vertices[edge_index]
            p2 = vertices[(edge_index + 1) % 6]
            dist = distance_to_polyline(cx, cy, [p1, p2])
            if dist is None or dist > tolerance:
                continue
            if best is None or dist < best[1]:
                best = (edge_index, dist)
        if best is None:
            return None
        return ((q, r), best[0])

    def pick_painted_edge(self, cx: float, cy: float) -> tuple[Coord, int] | None:
        edge = self.pick_edge(cx, cy)
        if edge is None:
            return None
        coord, edge_index = edge
        data = self._canvas._state.edges.get(coord)
        if not data:
            return None
        if int(data.get("edges", 0)) & (1 << edge_index):
            return edge
        return None

    def pick_description_at_point(self, cx: float, cy: float) -> Coord | None:
        coord = self.pick_hex(cx, cy)
        if coord is None:
            return None
        tile = self._canvas._state.tiles.get(coord)
        if not tile or not tile.get("description"):
            return None
        if self.point_hits_description(cx, cy, coord[0], coord[1], self._canvas._origin()):
            return coord
        return None

    def point_hits_description(
        self,
        cx: float,
        cy: float,
        q: int,
        r: int,
        origin: tuple[float, float],
    ) -> bool:
        bx, by = description_badge_center(origin, q, r, self._canvas._hex_size)
        radius = max(12.0, self._canvas._hex_size * 0.25)
        return (cx - bx) ** 2 + (cy - by) ** 2 <= radius**2

    def pick_path_id_at_point(self, cx: float, cy: float) -> str | None:
        ox, oy = self._canvas._origin()
        local_x = cx - ox
        local_y = cy - oy
        tolerance = max(12.0, self._canvas._hex_size * 0.22 + 8.0)
        best: tuple[float, str] | None = None
        for path in reversed(self._canvas._state.paths):
            for path_id, start, end in path_segments(path):
                start_px = hex_to_pixel(start[0], start[1], self._canvas._hex_size)
                end_px = hex_to_pixel(end[0], end[1], self._canvas._hex_size)
                distance = distance_to_polyline(local_x, local_y, [start_px, end_px])
                if distance is None or distance > tolerance:
                    continue
                if best is None or distance < best[0]:
                    best = (distance, path_id)
        return best[1] if best else None

    def pick_erase_component(self, cx: float, cy: float, q: int, r: int) -> str | None:
        tile = self._canvas._state.tiles.get((q, r))
        has_terrain = bool(tile.get("terrain")) if tile else False
        has_desc = bool(tile.get("description")) if tile else False
        if not has_terrain and not has_desc:
            return None
        if has_desc:
            origin = self._canvas._origin()
            if self.point_hits_description(cx, cy, q, r, origin):
                return "description"
        if has_terrain:
            return "terrain"
        if has_desc:
            return "description"
        return None

    def find_erase_target(
        self, cx: float, cy: float
    ) -> tuple[Coord, tuple | None] | None:
        desc_hit = self.pick_description_at_point(cx, cy)
        if desc_hit is not None:
            return desc_hit, ("description", desc_hit)
        path_id = self.pick_path_id_at_point(cx, cy)
        if path_id is not None:
            coord = self.pick_hex(cx, cy) or self.canvas_to_hex(cx, cy)
            return coord, ("path", path_id)
        edge = self.pick_painted_edge(cx, cy)
        if edge is not None:
            coord, edge_index = edge
            return coord, ("edge", coord, edge_index)
        coord = self.pick_hex(cx, cy)
        if coord is None:
            return None
        component = self.pick_erase_component(cx, cy, *coord)
        if component is None:
            return coord, None
        return coord, (component, coord)
