import math

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter

from models.geometry import Coord, hex_neighbors, hex_to_pixel
from views.map.canvas.layers.paint_context import PaintContext

class Renderer:
    def __init__(self, canvas) -> None:
        self._canvas = canvas

    def paint(self, painter: QPainter) -> None:
        from views.map.canvas.map_canvas import _BG

        c = self._canvas
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(c.rect(), _BG)
        self._paint_map(painter, origin=c._origin(), include_transient=True)

    def _paint_map(
        self,
        painter: QPainter,
        *,
        origin: tuple[float, float],
        include_transient: bool,
        minimap: bool = False,
    ) -> None:
        ctx = self._paint_context(
            painter,
            origin=origin,
            include_transient=include_transient,
            minimap=minimap,
        )
        c = self._canvas
        c._tile_layer.paint(ctx)
        c._path_layer.paint(ctx)
        c._edge_layer.paint(ctx)
        c._hint_layer.paint(ctx)
        c._description_layer.paint(ctx)

    def _paint_context(
        self,
        painter: QPainter,
        *,
        origin: tuple[float, float],
        include_transient: bool,
        minimap: bool,
    ) -> PaintContext:
        c = self._canvas
        extra_hexes = self._extra_preview_hexes() if include_transient else set()
        preview_coords = self._current_path_preview() if include_transient else []
        if (
            include_transient
            and c._path_mode
            and c._path_submode == "path"
            and c._current_path
        ):
            if c._path_hint_dirty:
                c._path_hint_cache = {
                    coord
                    for coord in hex_neighbors(*c._current_path[-1])
                    if c._input.can_continue_path_at(coord)
                }
                c._path_hint_dirty = False
            path_hint_next = c._path_hint_cache
        else:
            path_hint_next = set()
        return PaintContext(
            painter=painter,
            origin=origin,
            hex_size=c._hex_size,
            tiles=c._state.tiles,
            paths=c._state.paths,
            edges=c._state.edges,
            extra_hexes=extra_hexes,
            include_transient=include_transient,
            minimap=minimap,
            selected=c._selected,
            hover=c._hover,
            hover_component=c._hover_component,
            erase_mode=c._erase_mode,
            path_preview=preview_coords,
            path_mode=c._path_mode,
            path_submode=c._path_submode,
            path_color=c._path_color,
            hover_path_id=c._hover_path_id if include_transient else None,
            hover_edge=c._hover_edge,
            current_path=list(c._current_path),
            path_hint_next_hexes=path_hint_next,
        )

    def _extra_preview_hexes(self) -> set[Coord]:
        c = self._canvas
        coords: set[Coord] = set()
        if c._pick_any_hex and c._hover is not None:
            coords.add(c._hover)
        if c._path_mode and c._path_submode == "path":
            coords.update(c._current_path)
            if c._current_path:
                for coord in hex_neighbors(*c._current_path[-1]):
                    if c._input.can_continue_path_at(coord):
                        coords.add(coord)
        return coords

    def _current_path_preview(self) -> list[Coord]:
        c = self._canvas
        if not c._current_path:
            return []
        if c._hover is not None and c._input.can_continue_path_at(c._hover):
            return [*c._current_path, c._hover]
        return list(c._current_path)

    def export_full_map_image(self) -> QImage:
        from views.map.canvas.map_canvas import _BG, _EXPORT_HEX_SIZE

        c = self._canvas
        coords = c._state.export_coords()
        if not coords:
            return QImage()

        export_hex_size = _EXPORT_HEX_SIZE * self._export_scale()
        saved_hex_size = c._hex_size
        updates_enabled = c.updatesEnabled()
        c.setUpdatesEnabled(False)
        try:
            c._hex_size = export_hex_size
            bounds = self._export_bounds(coords, c._hex_size)
            if bounds is None:
                return QImage()
            min_x, min_y, width, height = bounds
            image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
            if image.isNull():
                return image
            image.fill(_BG)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            try:
                self._paint_map(
                    painter,
                    origin=(-min_x, -min_y),
                    include_transient=False,
                )
            finally:
                painter.end()
            return image
        finally:
            c._hex_size = saved_hex_size
            c.setUpdatesEnabled(updates_enabled)

    def _export_scale(self) -> float:
        from views.map.canvas.map_canvas import _EXPORT_SCALE_MIN

        return max(1.0, self._canvas.devicePixelRatioF(), _EXPORT_SCALE_MIN)

    def minimap_hex_size_for(
        self,
        target_w: float,
        target_h: float,
        *,
        min_hex: float = 8.0,
    ) -> float:
        c = self._canvas
        coords = c._state.export_coords()
        if not coords or target_w <= 0 or target_h <= 0:
            return min_hex
        lo = min_hex
        hi = max(min_hex, target_w, target_h) * 2.0
        result = hi
        for _ in range(32):
            mid = (lo + hi) / 2.0
            bounds = self._export_bounds(coords, mid)
            if bounds is None:
                hi = mid
                continue
            _min_x, _min_y, width, height = bounds
            if width >= target_w and height >= target_h:
                result = mid
                hi = mid
            else:
                lo = mid
        return max(min_hex, result)

    def render_minimap_image(
        self,
        hex_size: float = 8.0,
    ) -> tuple[QImage, float, float, float, float] | None:
        from views.map.canvas.map_canvas import _BG

        c = self._canvas
        coords = c._state.export_coords()
        if not coords:
            return None
        saved_hex_size = c._hex_size
        try:
            c._hex_size = hex_size
            bounds = self._export_bounds(coords, hex_size)
            if bounds is None:
                return None
            min_x, min_y, width, height = bounds
            image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
            if image.isNull():
                return None
            image.fill(_BG)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            try:
                self._paint_map(
                    painter,
                    origin=(-min_x, -min_y),
                    include_transient=False,
                    minimap=True,
                )
            finally:
                painter.end()
            return image, min_x, min_y, float(width), float(height)
        finally:
            c._hex_size = saved_hex_size

    def viewport_rect_in_map_image(
        self,
        map_hex_size: float,
        map_min_x: float,
        map_min_y: float,
    ) -> QRectF:
        c = self._canvas
        if c.width() <= 0 or c.height() <= 0:
            return QRectF()
        scale = map_hex_size / c._hex_size
        ox, oy = c._origin()
        vis_left = (-ox * scale) - map_min_x
        vis_top = (-oy * scale) - map_min_y
        vis_w = c.width() * scale
        vis_h = c.height() * scale
        return QRectF(vis_left, vis_top, vis_w, vis_h)

    def pan_to_map_image_point(
        self,
        image_x: float,
        image_y: float,
        map_hex_size: float,
        map_min_x: float,
        map_min_y: float,
    ) -> None:
        c = self._canvas
        scale = c._hex_size / map_hex_size
        gx = (image_x + map_min_x) * scale
        gy = (image_y + map_min_y) * scale
        c._offset[0] = c.width() / 2 - gx
        c._offset[1] = c.height() / 2 - gy
        c._emit_viewport_changed()
        c.update()

    @staticmethod
    def _export_bounds(
        coords: set[Coord],
        hex_size: float,
    ) -> tuple[float, float, int, int] | None:
        if not coords:
            return None
        centers = [hex_to_pixel(q, r, hex_size) for q, r in coords]
        margin = max(16.0, hex_size * 2.0)
        min_x = min(x for x, _y in centers) - margin
        max_x = max(x for x, _y in centers) + margin
        min_y = min(y for _x, y in centers) - margin
        max_y = max(y for _x, y in centers) + margin
        width = max(1, math.ceil(max_x - min_x))
        height = max(1, math.ceil(max_y - min_y))
        return min_x, min_y, width, height
