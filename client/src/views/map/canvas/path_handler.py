from models.geometry import Coord, _segment_key, axial_step_direction

class PathHandler:
    def __init__(self, canvas) -> None:
        self._canvas = canvas

    def handle_hex_click(self, coord: Coord) -> None:
        c = self._canvas
        if not c._current_path:
            c._current_path = [coord]
            c._path_hint_dirty = True
            c.current_path_points_changed.emit(1)
            return
        last = c._current_path[-1]
        before_last = c._current_path[-2] if len(c._current_path) >= 2 else None
        if coord == last:
            return
        if before_last is not None and coord == before_last:
            c._current_path.pop()
            c._path_hint_dirty = True
            c.current_path_points_changed.emit(len(c._current_path))
            return
        if not self._can_add_segment(last, coord):
            return
        c._current_path.append(coord)
        c._path_hint_dirty = True
        c.current_path_points_changed.emit(len(c._current_path))

    def can_continue_at(self, coord: Coord) -> bool:
        c = self._canvas
        if not (c._path_mode and c._path_submode == "path" and c._current_path):
            return False
        last = c._current_path[-1]
        if coord == last:
            return False
        return self._can_add_segment(last, coord)

    def _can_add_segment(self, start: Coord, end: Coord) -> bool:
        direction = axial_step_direction(start[0], start[1], end[0], end[1])
        reverse_direction = axial_step_direction(end[0], end[1], start[0], start[1])
        if direction is None or reverse_direction is None:
            return False
        segments = self._current_path_segments()
        if _segment_key(start, end) in segments:
            return False
        if self._direction_mask(start) & (1 << direction):
            return False
        if self._direction_mask(end) & (1 << reverse_direction):
            return False
        return True

    def _current_path_segments(self) -> set[tuple[Coord, Coord]]:
        path = self._canvas._current_path
        return {_segment_key(s, e) for s, e in zip(path, path[1:])}

    def _direction_mask(self, coord: Coord) -> int:
        mask = 0
        path = self._canvas._current_path
        for start, end in zip(path, path[1:]):
            if start == coord:
                direction = axial_step_direction(start[0], start[1], end[0], end[1])
            elif end == coord:
                direction = axial_step_direction(end[0], end[1], start[0], start[1])
            else:
                continue
            if direction is not None:
                mask |= 1 << direction
        return mask
