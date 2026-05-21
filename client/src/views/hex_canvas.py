from pathlib import Path

from PyQt6.QtCore import Qt, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QWidget

from geometry import Coord, hex_to_pixel, hex_vertices, pixel_to_hex
from models.asset_registry import REGISTRY

_ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"
_DESC_ICON_CACHE: dict[int, QPixmap] = {}


def _desc_hover_icon(size: int) -> QPixmap:
    if size not in _DESC_ICON_CACHE:
        raw = QIcon(str(_ICONS_DIR / "scroll-text.svg")).pixmap(QSize(size, size))
        if raw.isNull():
            _DESC_ICON_CACHE[size] = raw
            return raw
        tinted = QPixmap(raw.size())
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.drawPixmap(0, 0, raw)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), _DESC_DOT_COLOR)
        p.end()
        _DESC_ICON_CACHE[size] = tinted
    return _DESC_ICON_CACHE[size]


_HEX_SIZE_MIN = 20.0
_HEX_SIZE_MAX = 80.0
_HEX_SIZE_DEFAULT = 40.0
_ZOOM_STEP = 4.0
_ROAD_WIDTH = 3

_BG                 = QColor("#09090b")
_EMPTY_FILL         = QColor("#18181b")
_EMPTY_BORDER       = QColor("#3f3f46")
_FILLED_FILL        = QColor("#1c2d10")
_FILLED_BORDER      = QColor("#5ea500")
_HOVER_FILL         = QColor("#222c18")
_ERASE_HOVER_FILL   = QColor("#2d1212")
_ERASE_HOVER_BORDER = QColor("#ef4444")
_SELECTED_BORDER    = QColor("#d8f999")
_DESC_DOT_COLOR     = QColor("#3b82f6")

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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: dict[Coord, dict] = {}
        self._selected: Coord | None = None
        self._hover: Coord | None = None
        self._hover_component: str | None = None   # "structure"|"road"|"description"
        self._offset = [0.0, 0.0]
        self._hex_size = _HEX_SIZE_DEFAULT
        self._pan_anchor: tuple[float, float, float, float] | None = None
        self._pick_any_hex = False
        self._erase_mode = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background: #0a0a0b;")

    # ------------------------------------------------------------------
    # Public API
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
        self._selected = None
        self._hover = None
        self._hover_component = None
        self.update()

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
        self.update()

    def set_pick_any_hex(self, enabled: bool) -> None:
        self._pick_any_hex = enabled
        if not enabled and self._hover is not None and self._hover not in self._tiles:
            self._hover = None
            self._hover_component = None
            self.update()

    def tile_at(self, q: int, r: int) -> dict | None:
        return self._tiles.get((q, r))

    def road_id_at(self, q: int, r: int) -> str | None:
        road = (self._tiles.get((q, r)) or {}).get("road") or {}
        return road.get("id") or None

    def hovered_erase_component(self) -> str | None:
        return self._hover_component

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

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), _BG)
        for (q, r), data in self._tiles.items():
            self._draw_hex(painter, q, r, data)
        if (
            self._pick_any_hex
            and self._hover is not None
            and self._hover not in self._tiles
        ):
            self._draw_hex(painter, self._hover[0], self._hover[1], {})

    def _origin(self) -> tuple[float, float]:
        return (self.width() / 2 + self._offset[0], self.height() / 2 + self._offset[1])

    def _draw_hex(self, painter: QPainter, q: int, r: int, data: dict) -> None:
        ox, oy = self._origin()
        px, py = hex_to_pixel(q, r, self._hex_size)
        cx, cy = ox + px, oy + py

        poly = self._make_polygon(cx, cy, self._hex_size - 1.5)
        structure = data.get("structure")
        is_selected = self._selected == (q, r)
        is_hover = self._hover == (q, r)

        # In erase mode, the hovered component drives visual feedback.
        erase_comp = self._hover_component if (is_hover and self._erase_mode) else None

        # ---- Fill ----
        if structure:
            fill = _STRUCTURE_COLORS.get(structure.get("type", ""), _FILLED_FILL)
            if erase_comp == "structure":
                painter.setBrush(_ERASE_HOVER_FILL)
            elif is_hover and not self._erase_mode:
                painter.setBrush(fill.lighter(115))
            else:
                painter.setBrush(fill)
        elif erase_comp is not None:
            # road-only or description-only tile in erase hover — no dark fill,
            # the component indicator itself carries the red signal
            painter.setBrush(_EMPTY_FILL)
        elif is_hover and not self._erase_mode:
            painter.setBrush(_HOVER_FILL)
        else:
            painter.setBrush(_EMPTY_FILL)

        # ---- Border ----
        if is_selected:
            painter.setPen(QPen(_SELECTED_BORDER, 2.5))
        elif erase_comp is not None:
            # Always show red border so the user knows a click will erase
            painter.setPen(QPen(_ERASE_HOVER_BORDER, 2.0))
        elif structure:
            painter.setPen(QPen(_FILLED_BORDER, 1.0))
        else:
            painter.setPen(QPen(_EMPTY_BORDER, 1.0, Qt.PenStyle.DashLine))

        painter.drawPolygon(poly)

        # ---- Overlay tile image ----
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

        # ---- Road indicator ----
        if data.get("road"):
            if erase_comp == "road":
                road_color = _ERASE_HOVER_BORDER
                road_w = _ROAD_WIDTH + 2
            else:
                road_color = QColor(data["road"].get("color", "#5ea500"))
                road_w = _ROAD_WIDTH
            pen = QPen(road_color, road_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            hw = self._hex_size * 0.35
            painter.drawLine(QPointF(cx - hw, cy), QPointF(cx + hw, cy))

        # ---- Description indicator ----
        if data.get("description"):
            if erase_comp == "description":
                dot_color = _ERASE_HOVER_BORDER
                r_dot = self._hex_size * 0.13
            else:
                dot_color = _DESC_DOT_COLOR
                r_dot = self._hex_size * 0.08
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dot_color)
            painter.drawEllipse(
                QPointF(cx + self._hex_size * 0.35, cy + self._hex_size * 0.45),
                r_dot, r_dot,
            )
            # Scroll icon only in normal hover (not erase mode)
            if is_hover and not self._erase_mode:
                icon_size = max(12, round(self._hex_size * 0.45))
                ipx = _desc_hover_icon(icon_size)
                if not ipx.isNull():
                    painter.drawPixmap(
                        round(cx) - icon_size // 2,
                        round(cy) - icon_size // 2,
                        ipx,
                    )

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
            hit = self._pick_hex(x, y)
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
        needs_update = self._hover != hit
        if needs_update:
            self._hover = hit

        # In erase mode, update the sub-component even on intra-hex movement.
        if self._erase_mode:
            comp = self._pick_erase_component(x, y, *hit) if hit is not None else None
            if comp != self._hover_component:
                self._hover_component = comp
                needs_update = True

        if needs_update:
            self.update()
            if hit is not None and not self._erase_mode:
                self.hex_hovered.emit(hit[0], hit[1])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._pan_anchor = None
            self.setCursor(Qt.CursorShape.CrossCursor)
            return
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _canvas_to_hex(self, cx: float, cy: float) -> Coord:
        ox, oy = self._origin()
        return pixel_to_hex(cx - ox, cy - oy, self._hex_size)

    def _pick_hex(self, cx: float, cy: float) -> Coord | None:
        """Hex under cursor. Select mode: only painted tiles. Paint mode: any cell."""
        if not self._pick_any_hex and not self._tiles:
            return None
        q, r = self._canvas_to_hex(cx, cy)
        if not self._pick_any_hex and (q, r) not in self._tiles:
            return None
        ox, oy = self._origin()
        hpx, hpy = hex_to_pixel(q, r, self._hex_size)
        dist_sq = (cx - ox - hpx) ** 2 + (cy - oy - hpy) ** 2
        if dist_sq > (self._hex_size * 0.92) ** 2:
            return None
        return (q, r)

    def _pick_erase_component(self, cx: float, cy: float, q: int, r: int) -> str | None:
        """Which component is under the cursor within hex (q, r) when in erase mode."""
        tile = self._tiles.get((q, r))
        if not tile:
            return None

        ox, oy = self._origin()
        hpx, hpy = hex_to_pixel(q, r, self._hex_size)
        # cursor coords relative to the hex centre
        lx = cx - (ox + hpx)
        ly = cy - (oy + hpy)

        has_structure = bool(tile.get("structure"))
        has_road      = bool(tile.get("road"))
        has_desc      = bool(tile.get("description"))

        # Description dot lives at (+0.35*s, +0.45*s) — check proximity first.
        if has_desc:
            ddx, ddy = self._hex_size * 0.35, self._hex_size * 0.45
            if ((lx - ddx) ** 2 + (ly - ddy) ** 2) ** 0.5 < self._hex_size * 0.28:
                return "description"

        # Road occupies a horizontal band through the centre.
        if has_road and abs(ly) < self._hex_size * 0.22:
            return "road"

        # Fallback: largest remaining component in priority order.
        if has_structure:
            return "structure"
        if has_road:
            return "road"
        if has_desc:
            return "description"
        return None
