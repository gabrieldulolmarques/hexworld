import math
from pathlib import Path

from PyQt6.QtCore import Qt, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QWidget

from geometry import (
    Coord,
    axial_step_direction,
    distance_to_polyline,
    hex_neighbors,
    hex_to_pixel,
    hex_vertices,
    pixel_to_hex,
)
from models.asset_registry import REGISTRY
from models.path_style import (
    PathStyle,
    paint_pixel_segments,
    road_style,
)

_ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"
_DESC_ICON_CACHE: dict[tuple[int, str], QPixmap] = {}


def _desc_icon(size: int, color: QColor) -> QPixmap:
    key = (size, color.name())
    if key not in _DESC_ICON_CACHE:
        raw = QIcon(str(_ICONS_DIR / "scroll-text.svg")).pixmap(QSize(size, size))
        if raw.isNull():
            _DESC_ICON_CACHE[key] = raw
            return raw
        tinted = QPixmap(raw.size())
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.drawPixmap(0, 0, raw)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), color)
        p.end()
        _DESC_ICON_CACHE[key] = tinted
    return _DESC_ICON_CACHE[key]


_HEX_SIZE_MIN = 20.0
_HEX_SIZE_MAX = 80.0
_HEX_SIZE_DEFAULT = 40.0
_ZOOM_STEP = 4.0

_BG                 = QColor("#09090b")
_EMPTY_FILL         = QColor("#18181b")
_EMPTY_BORDER       = QColor("#3f3f46")
_FILLED_FILL        = QColor("#1c2d10")
_FILLED_BORDER      = QColor("#3f3f46")
_HOVER_FILL         = QColor("#222c18")
_ERASE_HOVER_FILL   = QColor("#2d1212")
_ERASE_HOVER_BORDER = QColor("#ef4444")
_SELECTED_BORDER    = QColor("#d8f999")
_DESC_BADGE_FILL    = QColor("#facc15")
_DESC_BADGE_BORDER  = QColor("#18181b")
_DESC_BADGE_ICON    = QColor("#18181b")
_DESC_BADGE_SHADOW  = QColor(0, 0, 0, 150)
_DESC_ERASE_ICON    = QColor("#fff7ed")
_ROAD_HINT_FILL     = QColor(94, 165, 0, 42)
_ROAD_HINT_BORDER   = QColor("#7ccf00")
_ROAD_NEXT_FILL     = QColor(94, 165, 0, 22)
_INNER_EDGE_INSET_RATIO = 0.84

_STRUCTURE_COLORS: dict[str, QColor] = {
    "castle":   QColor("#8b5cf6"),
    "village":  QColor("#f59e0b"),
    "fortress": QColor("#ef4444"),
    "ruins":    QColor("#6b7280"),
    "port":     QColor("#3b82f6"),
    "tower":    QColor("#f97316"),
}


class HexCanvas(QWidget):
    hex_clicked    = pyqtSignal(int, int)   # q, r — existing tile selected
    hex_deselected = pyqtSignal()
    hex_hovered    = pyqtSignal(int, int)   # q, r
    path_drawn     = pyqtSignal(list, str)  # waypoints, color
    road_drawn     = path_drawn             # alias
    inner_edge_painted = pyqtSignal(int, int, int, str)  # q, r, edge_index, color
    current_road_points_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Tile data (structure + description per coord)
        self._tiles: dict[Coord, dict] = {}
        # Road segments (map-level; same color forms a unified network)
        self._roads: list[dict] = []
        self._roads_by_coord: dict[Coord, str] = {}
        # Interaction state
        self._selected: Coord | None = None
        self._hover: Coord | None = None
        self._hover_component: str | None = None   # "structure"|"road"|"description"
        self._hover_road_id: str | None = None
        self._offset = [0.0, 0.0]
        self._hex_size = _HEX_SIZE_DEFAULT
        self._pan_anchor: tuple[float, float, float, float] | None = None
        self._pick_any_hex = False
        self._erase_mode = False
        self._brush_mode = False
        self._brush_active = False
        self._brush_seen_targets: set[tuple] = set()
        # Road-draw mode
        self._road_mode = False
        self._road_color = "#5ea500"
        self._road_submode = "curve"
        self._current_road: list[Coord] = []
        # Inner-edge segments are per-cell masks; each cell owns its own color.
        self._inner_edges: dict[Coord, dict] = {}
        self._hover_inner_edge: tuple[Coord, int] | None = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(400, 300)

    # ------------------------------------------------------------------
    # Public API — tiles
    # ------------------------------------------------------------------

    def set_tiles(self, tiles: dict[Coord, dict]) -> None:
        self._tiles = dict(tiles)
        if self._selected is not None and self._selected not in self._tiles:
            self._selected = None
        if self._hover is not None and self._hover not in self._tiles:
            self._hover = None
            self._hover_component = None
        self.update()

    def apply_tile(self, q: int, r: int, data: dict) -> None:
        self._tiles[(q, r)] = data
        self.update()

    def remove_tile(self, q: int, r: int) -> None:
        self._tiles.pop((q, r), None)
        if self._selected == (q, r):
            self._selected = None
        if self._hover == (q, r):
            self._hover_component = None
        self.update()

    def clear(self) -> None:
        self._tiles.clear()
        self._roads.clear()
        self._roads_by_coord.clear()
        self._inner_edges.clear()
        self._clear_current_road(emit=False)
        self._selected = None
        self._hover = None
        self._hover_component = None
        self._hover_road_id = None
        self._hover_inner_edge = None
        self.update()

    # ------------------------------------------------------------------
    # Public API — roads
    # ------------------------------------------------------------------

    def set_roads(self, roads: list[dict]) -> None:
        """Replace road segments (map state load)."""
        self._roads = list(roads)
        self._rebuild_roads_by_coord()
        self.update()

    def apply_road(self, road_id: str, waypoints: list, color: str) -> None:
        """Add or update one road segment (called on road_added event)."""
        self._roads = [r for r in self._roads if r["id"] != road_id]
        self._roads.append({"id": road_id, "waypoints": waypoints, "color": color})
        self._rebuild_roads_by_coord()
        self.update()

    def remove_road_by_id(self, road_id: str) -> None:
        """Remove one road by id (called on road_removed event)."""
        self._roads = [r for r in self._roads if r["id"] != road_id]
        self._rebuild_roads_by_coord()
        self.update()

    def road_id_at(self, q: int, r: int) -> str | None:
        """Return the road_id of any road passing through (q, r)."""
        return self._roads_by_coord.get((q, r))

    def road_at(self, q: int, r: int) -> dict | None:
        """Return the path dict at (q, r), if any."""
        rid = self.road_id_at(q, r)
        if rid is None:
            return None
        return self.road_by_id(rid)

    def road_segments_at(self, q: int, r: int) -> list[dict]:
        """Road segments that start or end on this hex (for inspector)."""
        coord = (q, r)
        found: list[dict] = []
        for road in self._roads:
            road_id = road.get("id", "")
            color = road.get("color", "#5ea500")
            for segment_id, start, end in self._road_segments(road):
                if start == coord or end == coord:
                    found.append({
                        "road_id": segment_id or road_id,
                        "color": color,
                        "start": start,
                        "end": end,
                    })
        return found

    def road_by_id(self, road_id: str) -> dict | None:
        """Return the road dict by id, if present."""
        for road in self._roads:
            if road["id"] == road_id:
                return road
        return None

    def road_ids(self) -> set[str]:
        """Return the current road ids."""
        return {road["id"] for road in self._roads if road.get("id")}

    # ------------------------------------------------------------------
    # Public API — inner edges
    # ------------------------------------------------------------------

    def set_inner_edges(self, cells: list[dict]) -> None:
        self._inner_edges = {}
        for cell in cells:
            q, r = cell.get("q"), cell.get("r")
            edges = int(cell.get("edges", 0) or 0)
            if q is None or r is None or edges <= 0:
                continue
            self._inner_edges[(int(q), int(r))] = {
                "edges": edges & 0b111111,
                "color": cell.get("color", "#5ea500"),
            }
        self.update()

    def apply_inner_edge_cell(self, cell: dict) -> None:
        q, r = cell.get("q"), cell.get("r")
        if q is None or r is None:
            return
        coord = (int(q), int(r))
        edges = int(cell.get("edges", 0) or 0) & 0b111111
        if edges:
            self._inner_edges[coord] = {
                "edges": edges,
                "color": cell.get("color", "#5ea500"),
            }
        else:
            self._inner_edges.pop(coord, None)
        self.update()

    def inner_edge_cell(self, q: int, r: int) -> dict | None:
        cell = self._inner_edges.get((q, r))
        return dict(cell) if cell else None

    # ------------------------------------------------------------------
    # Public API — interaction modes
    # ------------------------------------------------------------------

    def set_selected(self, coord: Coord | None) -> None:
        self._selected = coord
        self.update()

    def clear_selection(self) -> None:
        if self._selected is None:
            return
        self._selected = None
        self.update()

    def set_erase_mode(self, enabled: bool) -> None:
        self._erase_mode = enabled
        if not enabled:
            self._hover_component = None
            self._hover_road_id = None
            self._brush_active = False
            self._brush_seen_targets.clear()
        self.update()

    def set_brush_mode(self, enabled: bool) -> None:
        self._brush_mode = enabled
        if not enabled:
            self._brush_active = False
            self._brush_seen_targets.clear()

    def set_pick_any_hex(self, enabled: bool) -> None:
        self._pick_any_hex = enabled
        if not enabled and self._hover is not None and self._hover not in self._tiles:
            self._hover = None
            self._hover_component = None
            self.update()

    def set_road_mode(self, enabled: bool, color: str = "") -> None:
        self._road_mode = enabled
        if color:
            self._road_color = color
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
            self._clear_current_road()
            self._hover_inner_edge = None
        self.update()

    def set_road_submode(self, submode: str) -> None:
        if submode not in ("curve", "inner_edge"):
            return
        self._road_submode = submode
        if submode != "inner_edge":
            self._hover_inner_edge = None
        self.update()

    def set_road_color(self, color: str) -> None:
        self._road_color = color

    def start_new_road(self) -> None:
        self._clear_current_road()

    def undo_current_road_point(self) -> None:
        if not self._current_road:
            return
        self._current_road.pop()
        self.current_road_points_changed.emit(len(self._current_road))
        self.update()

    def finish_current_road(self) -> None:
        if len(self._current_road) < 2:
            return
        waypoints = [[q, r] for q, r in self._current_road]
        color = self._road_color
        self._clear_current_road()
        self.path_drawn.emit(waypoints, color)

    def cancel_current_road(self) -> None:
        self._clear_current_road()

    def tile_at(self, q: int, r: int) -> dict | None:
        return self._tiles.get((q, r))

    def hovered_erase_component(self) -> str | None:
        return self._hover_component

    def hovered_road_id(self) -> str | None:
        return self._hover_road_id

    def hovered_inner_edge(self) -> tuple[Coord, int] | None:
        return self._hover_inner_edge

    def description_text(self, q: int, r: int) -> str:
        tile = self._tiles.get((q, r), {})
        desc = tile.get("description") or {}
        return desc.get("text", "")

    def zoom_in(self) -> None:
        self._hex_size = min(_HEX_SIZE_MAX, self._hex_size + _ZOOM_STEP)
        self.update()

    def zoom_out(self) -> None:
        self._hex_size = max(_HEX_SIZE_MIN, self._hex_size - _ZOOM_STEP)
        self.update()

    def export_full_map_image(self) -> QImage:
        """Render the complete persistent map to an offscreen image."""
        coords = self._export_coords()
        if not coords:
            return self.grab().toImage()

        bounds = self._export_bounds(coords, self._hex_size)
        if bounds is None:
            return QImage()

        min_x, min_y, width, height = bounds

        image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        if image.isNull():
            return image
        image.fill(_BG)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            self._paint_map(
                painter,
                origin=(-min_x, -min_y),
                include_transient=False,
            )
        finally:
            painter.end()
        return image

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), _BG)
        self._paint_map(painter, origin=self._origin(), include_transient=True)

    def _paint_map(
        self,
        painter: QPainter,
        *,
        origin: tuple[float, float],
        include_transient: bool,
    ) -> None:
        # 1) Hex fills and borders (no structure sprites)
        for (q, r), data in self._tiles.items():
            self._draw_hex(
                painter, q, r, data,
                origin=origin,
                overlay=False,
                include_transient=include_transient,
            )

        extra_hexes = self._extra_preview_hexes() if include_transient else set()
        for q, r in extra_hexes:
            if (q, r) not in self._tiles:
                self._draw_hex(
                    painter, q, r, {},
                    origin=origin,
                    overlay=False,
                    include_transient=include_transient,
                )

        # 2) Structure sprites
        for (q, r), data in self._tiles.items():
            self._draw_hex(
                painter, q, r, data,
                origin=origin,
                overlay=True,
                include_transient=include_transient,
            )

        for q, r in extra_hexes:
            if (q, r) not in self._tiles:
                self._draw_hex(
                    painter, q, r, {},
                    origin=origin,
                    overlay=True,
                    include_transient=include_transient,
                )

        # 3) Roads (above tile fills and structure sprites)
        hover_road_id: str | None = None
        if include_transient and self._erase_mode and self._hover_component == "road":
            hover_road_id = self._hover_road_id

        for color, segments in self._road_segments_by_color().items():
            self._paint_road_segments(painter, origin, segments, color)

        if hover_road_id:
            hover_segments = self._road_segments_for_id(hover_road_id)
            if hover_segments:
                self._paint_road_segments(
                    painter, origin, hover_segments, "#ef4444",
                    highlight=True,
                )

        # 4) Inner edges
        self._draw_inner_edges(
            painter,
            origin=origin,
            include_transient=include_transient,
        )

        # 5) Road draw hover hints above painted hexes.
        if include_transient:
            self._draw_road_hint_overlay(painter, origin)

        # 6) Current road preview
        preview_coords = self._current_road_preview() if include_transient else []
        if (
            include_transient
            and self._road_mode
            and self._road_submode == "curve"
            and len(preview_coords) >= 2
        ):
            self._paint_road_segments(
                painter, origin,
                self._segments_from_waypoints(preview_coords),
                self._road_color,
                preview=True,
            )

        # 7) Descriptions stay on the topmost overlay.
        self._draw_descriptions(
            painter,
            origin=origin,
            include_transient=include_transient,
        )

    def _origin(self) -> tuple[float, float]:
        return (self.width() / 2 + self._offset[0], self.height() / 2 + self._offset[1])

    def _draw_hex(
        self,
        painter: QPainter,
        q: int,
        r: int,
        data: dict,
        *,
        origin: tuple[float, float],
        overlay: bool,
        include_transient: bool,
    ) -> None:
        ox, oy = origin
        px, py = hex_to_pixel(q, r, self._hex_size)
        cx, cy = ox + px, oy + py

        poly = self._make_polygon(cx, cy, self._hex_size - 1.5)
        structure = data.get("structure")
        is_selected = include_transient and self._selected == (q, r)
        is_hover = include_transient and self._hover == (q, r)
        erase_comp = (
            self._hover_component
            if (include_transient and is_hover and self._erase_mode)
            else None
        )

        if not overlay:
            self._draw_hex_fill(
                painter, poly, (q, r), structure, is_selected, is_hover, erase_comp,
                include_transient=include_transient,
            )
            return

        self._draw_hex_overlay(
            painter, cx, cy, poly, data, structure, is_selected, is_hover, erase_comp,
            include_transient=include_transient,
        )

    def _draw_hex_fill(
        self,
        painter: QPainter,
        poly: QPolygonF,
        coord: Coord,
        structure: dict | None,
        is_selected: bool,
        is_hover: bool,
        erase_comp: str | None,
        *,
        include_transient: bool,
    ) -> None:
        if structure:
            fill = _STRUCTURE_COLORS.get(structure.get("type", ""), _FILLED_FILL)
            if erase_comp == "structure":
                painter.setBrush(_ERASE_HOVER_FILL)
            elif is_hover and not self._erase_mode:
                painter.setBrush(fill.lighter(115))
            else:
                painter.setBrush(fill)
        elif erase_comp is not None:
            # road-only or description-only tile in erase hover — no dark fill
            painter.setBrush(_EMPTY_FILL)
        elif is_hover and not self._erase_mode:
            painter.setBrush(_HOVER_FILL)
        else:
            painter.setBrush(_EMPTY_FILL)

        # ---- Border ----
        if is_selected:
            painter.setPen(QPen(_SELECTED_BORDER, 2.5))
        elif erase_comp is not None:
            painter.setPen(QPen(_ERASE_HOVER_BORDER, 2.0))
        elif structure:
            painter.setPen(QPen(_FILLED_BORDER, 1.0))
        else:
            painter.setPen(QPen(_EMPTY_BORDER, 1.0, Qt.PenStyle.DashLine))

        painter.drawPolygon(poly)

    def _draw_hex_overlay(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        poly: QPolygonF,
        data: dict,
        structure: dict | None,
        is_selected: bool,
        is_hover: bool,
        erase_comp: str | None,
        *,
        include_transient: bool,
    ) -> None:
        if structure:
            stype = structure.get("type", "")
            tile_px = REGISTRY.pixmap(stype, self._hex_size)
            if tile_px is not None:
                size = round(self._hex_size)
                painter.drawPixmap(round(cx) - size, round(cy) - size, tile_px)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                if erase_comp == "structure":
                    painter.setPen(QPen(_ERASE_HOVER_BORDER, 2.0))
                else:
                    painter.setPen(QPen(
                        _SELECTED_BORDER if is_selected else _FILLED_BORDER,
                        2.5 if is_selected else 1.0,
                    ))
                painter.drawPolygon(poly)

    @staticmethod
    def _make_polygon(cx: float, cy: float, size: float) -> QPolygonF:
        return QPolygonF([QPointF(x, y) for x, y in hex_vertices(cx, cy, size)])

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        step = _ZOOM_STEP if delta > 0 else -_ZOOM_STEP
        self._hex_size = max(_HEX_SIZE_MIN, min(_HEX_SIZE_MAX, self._hex_size + step))
        self.update()
        event.accept()

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()

        if event.button() == Qt.MouseButton.LeftButton:
            if self._road_mode and self._road_submode == "curve":
                hit = self._pick_hex(x, y)
                if hit is None:
                    return
                self._handle_road_hex_click(hit)
                self._hover = hit
                self.update()
                return

            if self._road_mode and self._road_submode == "inner_edge":
                edge = self._pick_inner_edge(x, y)
                if edge is None:
                    return
                coord, edge_index = edge
                self._hover = coord
                self._hover_inner_edge = edge
                self.inner_edge_painted.emit(coord[0], coord[1], edge_index, self._road_color)
                self.update()
                return

            if self._brush_mode:
                self._brush_active = True
                self._brush_seen_targets.clear()
                self._apply_brush_at(x, y)
                return

            # Normal click — select or paint
            desc_hit = self._pick_description_at_point(x, y) if self._erase_mode else None
            road_hit = self._pick_road_id_at_point(x, y) if self._erase_mode else None
            inner_hit = self._pick_painted_inner_edge(x, y) if self._erase_mode else None
            hit = self._pick_hex(x, y)
            if self._erase_mode and desc_hit is not None:
                self._hover = desc_hit
                self._hover_road_id = None
                self._hover_inner_edge = None
                self._hover_component = "description"
                self.update()
                self.hex_clicked.emit(desc_hit[0], desc_hit[1])
                return
            if self._erase_mode and road_hit is not None:
                hit = hit or self._canvas_to_hex(x, y)
                self._hover = hit
                self._hover_road_id = road_hit
                self._hover_component = "road"
                self.update()
                self.hex_clicked.emit(hit[0], hit[1])
                return
            if self._erase_mode and inner_hit is not None:
                coord, _edge_index = inner_hit
                self._hover = coord
                self._hover_inner_edge = inner_hit
                self._hover_component = "inner_edge"
                self.update()
                self.hex_clicked.emit(coord[0], coord[1])
                return
            if hit is None:
                if self._selected is not None:
                    self._selected = None
                    self.update()
                    self.hex_deselected.emit()
                return
            if not self._pick_any_hex:
                if self._selected == hit:
                    self._selected = None
                    self.update()
                    self.hex_deselected.emit()
                    return
                self._selected = hit
            self.update()
            self.hex_clicked.emit(hit[0], hit[1])
            return

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._pan_anchor = (x, y, self._offset[0], self._offset[1])
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()

        if self._pan_anchor is not None:
            x0, y0, ox, oy = self._pan_anchor
            self._offset[0] = ox + (x - x0)
            self._offset[1] = oy + (y - y0)
            self.update()
            return

        hit = self._pick_hex(x, y)
        needs_update = False
        if self._road_mode and self._road_submode == "inner_edge":
            edge = self._pick_inner_edge(x, y)
            if edge is not None:
                hit = edge[0]
            if edge != self._hover_inner_edge:
                self._hover_inner_edge = edge
                needs_update = True

        if self._hover != hit:
            self._hover = hit
            needs_update = True

        # In erase mode, update the sub-component even on intra-hex movement.
        if self._erase_mode:
            desc_hit = self._pick_description_at_point(x, y)
            road_id = None
            inner_edge = None
            if desc_hit is not None:
                comp = "description"
                hit = desc_hit
                if self._hover != hit:
                    self._hover = hit
                    needs_update = True
            else:
                road_id = self._pick_road_id_at_point(x, y)
            if desc_hit is None and road_id is not None:
                comp = "road"
                if hit is None:
                    hit = self._canvas_to_hex(x, y)
                    self._hover = hit
                    needs_update = True
            elif desc_hit is None:
                inner_edge = self._pick_painted_inner_edge(x, y)
                if inner_edge is not None:
                    comp = "inner_edge"
                    hit = inner_edge[0]
                    if self._hover != hit:
                        self._hover = hit
                        needs_update = True
                else:
                    comp = self._pick_erase_component(x, y, *hit) if hit is not None else None
            if road_id != self._hover_road_id:
                self._hover_road_id = road_id
                needs_update = True
            if inner_edge != self._hover_inner_edge:
                self._hover_inner_edge = inner_edge
                needs_update = True
            if comp != self._hover_component:
                self._hover_component = comp
                needs_update = True

        if needs_update:
            self.update()
            if hit is not None and not self._erase_mode:
                self.hex_hovered.emit(hit[0], hit[1])
        if self._brush_active:
            self._apply_brush_at(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._brush_active:
            self._brush_active = False
            self._brush_seen_targets.clear()
            return
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._pan_anchor = None
            if self._road_mode:
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self.unsetCursor()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, _event) -> None:
        self._brush_active = False
        self._brush_seen_targets.clear()
        if self._hover is not None or self._hover_inner_edge is not None or self._hover_road_id:
            self._hover = None
            self._hover_component = None
            self._hover_road_id = None
            self._hover_inner_edge = None
            self.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _canvas_to_hex(self, cx: float, cy: float) -> Coord:
        ox, oy = self._origin()
        return pixel_to_hex(cx - ox, cy - oy, self._hex_size)

    def _pick_hex(self, cx: float, cy: float) -> Coord | None:
        """Hex under cursor. In erase mode also picks road-only hexes."""
        q, r = self._canvas_to_hex(cx, cy)
        loose = self._pick_any_hex or self._road_mode
        if not loose:
            in_tile = (q, r) in self._tiles
            in_road = self._erase_mode and (q, r) in self._roads_by_coord
            if not in_tile and not in_road:
                return None
            ox, oy = self._origin()
            hpx, hpy = hex_to_pixel(q, r, self._hex_size)
            dist_sq = (cx - ox - hpx) ** 2 + (cy - oy - hpy) ** 2
            if dist_sq > (self._hex_size * 0.92) ** 2:
                return None
        return (q, r)

    def _apply_brush_at(self, cx: float, cy: float) -> None:
        if self._erase_mode:
            target = self._erase_target_at(cx, cy)
        else:
            coord = self._pick_hex(cx, cy)
            target = (coord, ("paint", coord)) if coord is not None else None
            if coord is not None and self._hover != coord:
                self._hover = coord
                self.update()
        if target is None:
            return

        coord, target_key = target
        if target_key in self._brush_seen_targets:
            return
        self._brush_seen_targets.add(target_key)
        self.hex_clicked.emit(coord[0], coord[1])

    def _erase_target_at(self, cx: float, cy: float) -> tuple[Coord, tuple] | None:
        desc_hit = self._pick_description_at_point(cx, cy)
        if desc_hit is not None:
            self._set_erase_hover(desc_hit, "description")
            return desc_hit, ("description", desc_hit)

        road_id = self._pick_road_id_at_point(cx, cy)
        if road_id is not None:
            coord = self._pick_hex(cx, cy) or self._canvas_to_hex(cx, cy)
            self._set_erase_hover(coord, "road", road_id=road_id)
            return coord, ("road", road_id)

        inner_edge = self._pick_painted_inner_edge(cx, cy)
        if inner_edge is not None:
            coord, edge_index = inner_edge
            self._set_erase_hover(coord, "inner_edge", inner_edge=inner_edge)
            return coord, ("inner_edge", coord, edge_index)

        coord = self._pick_hex(cx, cy)
        if coord is None:
            self._set_erase_hover(None, None)
            return None
        component = self._pick_erase_component(cx, cy, *coord)
        self._set_erase_hover(coord, component)
        if component is None:
            return None
        return coord, (component, coord)

    def _set_erase_hover(
        self,
        coord: Coord | None,
        component: str | None,
        *,
        road_id: str | None = None,
        inner_edge: tuple[Coord, int] | None = None,
    ) -> None:
        changed = (
            self._hover != coord
            or self._hover_component != component
            or self._hover_road_id != road_id
            or self._hover_inner_edge != inner_edge
        )
        self._hover = coord
        self._hover_component = component
        self._hover_road_id = road_id
        self._hover_inner_edge = inner_edge
        if changed:
            self.update()

    def keyPressEvent(self, event) -> None:
        if not self._current_road:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_current_road()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.finish_current_road()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Backspace:
            self.undo_current_road_point()
            event.accept()
            return
        super().keyPressEvent(event)

    def _clear_current_road(self, *, emit: bool = True) -> None:
        if not self._current_road and emit:
            self.current_road_points_changed.emit(0)
            return
        self._current_road = []
        if emit:
            self.current_road_points_changed.emit(0)
        self.update()

    def _handle_road_hex_click(self, coord: Coord) -> None:
        if not self._current_road:
            self._current_road = [coord]
            self.current_road_points_changed.emit(1)
            return

        last = self._current_road[-1]
        before_last = self._current_road[-2] if len(self._current_road) >= 2 else None

        if coord == last:
            return
        if before_last is not None and coord == before_last:
            self._current_road.pop()
            self.current_road_points_changed.emit(len(self._current_road))
            return
        if not self._can_add_current_road_segment(last, coord):
            return
        self._current_road.append(coord)
        self.current_road_points_changed.emit(len(self._current_road))

    def _can_continue_road_at(self, coord: Coord) -> bool:
        if not (self._road_mode and self._road_submode == "curve" and self._current_road):
            return False
        last = self._current_road[-1]
        if coord == last:
            return False
        return self._can_add_current_road_segment(last, coord)

    def _extra_preview_hexes(self) -> set[Coord]:
        coords: set[Coord] = set()
        if self._pick_any_hex and self._hover is not None:
            coords.add(self._hover)
        if self._road_mode and self._road_submode == "curve":
            coords.update(self._current_road)
            if self._current_road:
                for coord in hex_neighbors(*self._current_road[-1]):
                    if self._can_continue_road_at(coord):
                        coords.add(coord)
        return coords

    def _current_road_preview(self) -> list[Coord]:
        if not self._current_road:
            return []
        if self._hover is not None and self._can_continue_road_at(self._hover):
            return [*self._current_road, self._hover]
        return list(self._current_road)

    @staticmethod
    def _segment_key(start: Coord, end: Coord) -> tuple[Coord, Coord]:
        return (start, end) if start <= end else (end, start)

    def _current_road_segments(self) -> set[tuple[Coord, Coord]]:
        return {
            self._segment_key(start, end)
            for start, end in zip(self._current_road, self._current_road[1:])
        }

    def _current_road_direction_mask(self, coord: Coord) -> int:
        """Six-bit Catlike-style road mask for the in-progress route at coord."""
        mask = 0
        for start, end in zip(self._current_road, self._current_road[1:]):
            if start == coord:
                direction = axial_step_direction(start[0], start[1], end[0], end[1])
            elif end == coord:
                direction = axial_step_direction(end[0], end[1], start[0], start[1])
            else:
                continue
            if direction is not None:
                mask |= 1 << direction
        return mask

    def _can_add_current_road_segment(self, start: Coord, end: Coord) -> bool:
        direction = axial_step_direction(start[0], start[1], end[0], end[1])
        reverse_direction = axial_step_direction(end[0], end[1], start[0], start[1])
        if direction is None or reverse_direction is None:
            return False
        if self._segment_key(start, end) in self._current_road_segments():
            return False
        if self._current_road_direction_mask(start) & (1 << direction):
            return False
        if self._current_road_direction_mask(end) & (1 << reverse_direction):
            return False
        return True

    def _inner_edge_size(self) -> float:
        return max(1.0, self._hex_size * _INNER_EDGE_INSET_RATIO)

    def _draw_road_hint_overlay(
        self,
        painter: QPainter,
        origin: tuple[float, float],
    ) -> None:
        if not (self._road_mode and self._road_submode == "curve"):
            return

        current = set(self._current_road)
        next_coords: set[Coord] = set()
        if self._current_road:
            for coord in hex_neighbors(*self._current_road[-1]):
                if self._can_continue_road_at(coord):
                    next_coords.add(coord)

        for coord in current:
            self._draw_road_hint_hex(
                painter, origin, coord,
                fill=_ROAD_HINT_FILL,
                pen=QPen(_ROAD_HINT_BORDER, 2.4),
            )
        for coord in next_coords - current:
            self._draw_road_hint_hex(
                painter, origin, coord,
                fill=_ROAD_NEXT_FILL,
                pen=QPen(_ROAD_HINT_BORDER, 1.4, Qt.PenStyle.DashLine),
            )

    def _draw_road_hint_hex(
        self,
        painter: QPainter,
        origin: tuple[float, float],
        coord: Coord,
        *,
        fill: QColor,
        pen: QPen,
    ) -> None:
        ox, oy = origin
        px, py = hex_to_pixel(coord[0], coord[1], self._hex_size)
        poly = self._make_polygon(ox + px, oy + py, self._hex_size - 1.5)
        painter.setBrush(fill)
        painter.setPen(pen)
        painter.drawPolygon(poly)

    def _draw_inner_edges(
        self,
        painter: QPainter,
        *,
        origin: tuple[float, float],
        include_transient: bool,
    ) -> None:
        for (q, r), data in self._inner_edges.items():
            edges = int(data.get("edges", 0))
            color = QColor(data.get("color", "#5ea500"))
            for edge_index in range(6):
                if edges & (1 << edge_index):
                    self._draw_inner_edge(
                        painter, origin, q, r, edge_index, color,
                        active=True,
                    )

        if (
            include_transient
            and self._road_mode
            and self._road_submode == "inner_edge"
            and self._hover_inner_edge is not None
        ):
            coord, edge_index = self._hover_inner_edge
            self._draw_inner_edge(
                painter, origin, coord[0], coord[1], edge_index,
                QColor(self._road_color), active=False,
            )
        elif (
            include_transient
            and self._erase_mode
            and self._hover_component == "inner_edge"
            and self._hover_inner_edge
        ):
            coord, edge_index = self._hover_inner_edge
            self._draw_inner_edge(
                painter, origin, coord[0], coord[1], edge_index,
                _ERASE_HOVER_BORDER, active=False,
            )

    def _draw_inner_edge(
        self,
        painter: QPainter,
        origin: tuple[float, float],
        q: int,
        r: int,
        edge_index: int,
        color: QColor,
        *,
        active: bool,
    ) -> None:
        ox, oy = origin
        px, py = hex_to_pixel(q, r, self._hex_size)
        vertices = hex_vertices(ox + px, oy + py, self._inner_edge_size())
        p1 = vertices[edge_index]
        p2 = vertices[(edge_index + 1) % 6]
        pen_color = QColor(color)
        if not active:
            pen_color = QColor(color)
            pen_color.setAlphaF(0.82)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(
            pen_color,
            max(2, round(self._hex_size * (0.09 if active else 0.075))),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        ))
        painter.drawLine(QPointF(*p1), QPointF(*p2))

    def _draw_descriptions(
        self,
        painter: QPainter,
        *,
        origin: tuple[float, float],
        include_transient: bool,
    ) -> None:
        for (q, r), data in self._tiles.items():
            if not data.get("description"):
                continue
            is_hover = include_transient and self._hover == (q, r)
            active = (
                include_transient
                and is_hover
                and self._erase_mode
                and self._hover_component == "description"
            )
            self._draw_description_badge(painter, origin, q, r, active=active)

    def _draw_description_badge(
        self,
        painter: QPainter,
        origin: tuple[float, float],
        q: int,
        r: int,
        *,
        active: bool,
    ) -> None:
        cx, cy = self._description_badge_center(origin, q, r)
        radius = max(8.0, self._hex_size * 0.17)
        fill = _ERASE_HOVER_BORDER if active else _DESC_BADGE_FILL
        border = _DESC_ERASE_ICON if active else _DESC_BADGE_BORDER
        icon_color = _DESC_ERASE_ICON if active else _DESC_BADGE_ICON

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_DESC_BADGE_SHADOW)
        painter.drawEllipse(QPointF(cx + 1.5, cy + 2.0), radius, radius)

        painter.setBrush(fill)
        painter.setPen(QPen(border, max(1.4, self._hex_size * 0.035)))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        icon_size = max(11, round(radius * 1.18))
        icon = _desc_icon(icon_size, icon_color)
        if not icon.isNull():
            painter.drawPixmap(
                round(cx) - icon_size // 2,
                round(cy) - icon_size // 2,
                icon,
            )

    def _pick_inner_edge(self, cx: float, cy: float) -> tuple[Coord, int] | None:
        q, r = self._canvas_to_hex(cx, cy)
        ox, oy = self._origin()
        px, py = hex_to_pixel(q, r, self._hex_size)
        vertices = hex_vertices(ox + px, oy + py, self._inner_edge_size())
        tolerance = max(8.0, self._hex_size * 0.18)
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

    def _pick_painted_inner_edge(self, cx: float, cy: float) -> tuple[Coord, int] | None:
        edge = self._pick_inner_edge(cx, cy)
        if edge is None:
            return None
        coord, edge_index = edge
        data = self._inner_edges.get(coord)
        if not data:
            return None
        if int(data.get("edges", 0)) & (1 << edge_index):
            return edge
        return None

    def _pick_description_at_point(self, cx: float, cy: float) -> Coord | None:
        coord = self._pick_hex(cx, cy)
        if coord is None:
            return None
        tile = self._tiles.get(coord)
        if not tile or not tile.get("description"):
            return None
        if self._point_hits_description(cx, cy, coord[0], coord[1], self._origin()):
            return coord
        return None

    def _point_hits_description(
        self,
        cx: float,
        cy: float,
        q: int,
        r: int,
        origin: tuple[float, float],
    ) -> bool:
        bx, by = self._description_badge_center(origin, q, r)
        radius = max(12.0, self._hex_size * 0.25)
        return (cx - bx) ** 2 + (cy - by) ** 2 <= radius ** 2

    def _description_badge_center(
        self,
        origin: tuple[float, float],
        q: int,
        r: int,
    ) -> tuple[float, float]:
        ox, oy = origin
        px, py = hex_to_pixel(q, r, self._hex_size)
        return (
            ox + px + self._hex_size * 0.38,
            oy + py + self._hex_size * 0.43,
        )

    def _pick_road_id_at_point(self, cx: float, cy: float) -> str | None:
        ox, oy = self._origin()
        local_x = cx - ox
        local_y = cy - oy
        tolerance = max(12.0, self._hex_size * 0.22 + 8.0)
        best: tuple[float, str] | None = None
        for road in reversed(self._roads):
            for road_id, start, end in self._road_segments(road):
                start_px = hex_to_pixel(start[0], start[1], self._hex_size)
                end_px = hex_to_pixel(end[0], end[1], self._hex_size)
                distance = distance_to_polyline(local_x, local_y, [start_px, end_px])
                if distance is None or distance > tolerance:
                    continue
                if best is None or distance < best[0]:
                    best = (distance, road_id)
        return best[1] if best else None

    def _pick_erase_component(self, cx: float, cy: float, q: int, r: int) -> str | None:
        """Which component is under the cursor within hex (q, r) when in erase mode."""
        tile = self._tiles.get((q, r))
        has_structure = bool(tile.get("structure")) if tile else False
        has_desc      = bool(tile.get("description")) if tile else False

        if not has_structure and not has_desc:
            return None

        if has_desc:
            origin = self._origin()
            if self._point_hits_description(cx, cy, q, r, origin):
                return "description"

        if has_structure:
            return "structure"
        if has_desc:
            return "description"
        return None

    def _export_coords(self) -> set[Coord]:
        coords: set[Coord] = set(self._tiles)
        coords.update(self._inner_edges)
        for road in self._roads:
            coords.update(self._road_waypoints(road))
        return coords

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

    def _rebuild_roads_by_coord(self) -> None:
        """Rebuild the coord→road_id lookup after any road list change."""
        self._roads_by_coord = {}
        for road in self._roads:
            for wp in road["waypoints"]:
                coord = (int(wp[0]), int(wp[1]))
                self._roads_by_coord[coord] = road["id"]

    def _paint_road_segments(
        self,
        painter: QPainter,
        origin: tuple[float, float],
        segments: list[tuple[Coord, Coord]],
        color: str,
        *,
        preview: bool = False,
        highlight: bool = False,
    ) -> None:
        pixel_segments = [
            (
                hex_to_pixel(start[0], start[1], self._hex_size),
                hex_to_pixel(end[0], end[1], self._hex_size),
            )
            for start, end in segments
        ]
        paint_pixel_segments(
            painter,
            origin,
            pixel_segments,
            self._hex_size,
            PathStyle(color=color) if highlight else road_style(color),
            preview=preview,
            highlight=highlight,
        )

    def _road_segments_by_color(self) -> dict[str, list[tuple[Coord, Coord]]]:
        by_color: dict[str, list[tuple[Coord, Coord]]] = {}
        for road in self._roads:
            color = road.get("color", "#5ea500")
            for _road_id, start, end in self._road_segments(road):
                by_color.setdefault(color, []).append((start, end))
        return by_color

    def _road_segments_for_id(self, road_id: str) -> list[tuple[Coord, Coord]]:
        segments: list[tuple[Coord, Coord]] = []
        for road in self._roads:
            for segment_id, start, end in self._road_segments(road):
                if segment_id == road_id:
                    segments.append((start, end))
        return segments

    def _road_segments(self, road: dict) -> list[tuple[str, Coord, Coord]]:
        road_id = road.get("id", "")
        return [
            (road_id, start, end)
            for start, end in self._segments_from_waypoints(self._road_waypoints(road))
        ]

    @staticmethod
    def _segments_from_waypoints(waypoints: list[Coord]) -> list[tuple[Coord, Coord]]:
        return [
            (start, end)
            for start, end in zip(waypoints, waypoints[1:])
            if start != end
        ]

    @staticmethod
    def _road_waypoints(road: dict) -> list[Coord]:
        return [(int(wp[0]), int(wp[1])) for wp in road.get("waypoints", [])]
