from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

from geometry import Coord, hex_to_pixel, hex_vertices, pixel_to_hex
from models.asset_registry import REGISTRY

_HEX_SIZE_MIN = 20.0
_HEX_SIZE_MAX = 80.0
_HEX_SIZE_DEFAULT = 40.0
_ZOOM_STEP = 4.0
_ROAD_WIDTH = 3

_BG                = QColor("#09090b")
_EMPTY_FILL        = QColor("#18181b")
_EMPTY_BORDER      = QColor("#3f3f46")
_FILLED_FILL       = QColor("#1c2d10")
_FILLED_BORDER     = QColor("#5ea500")
_HOVER_FILL        = QColor("#222c18")
_SELECTED_BORDER   = QColor("#d8f999")
_DESC_DOT_COLOR    = QColor("#3b82f6")

_STRUCTURE_COLORS: dict[str, QColor] = {
    "castle":   QColor("#8b5cf6"),
    "village":  QColor("#f59e0b"),
    "fortress": QColor("#ef4444"),
    "ruins":    QColor("#6b7280"),
    "port":     QColor("#3b82f6"),
    "tower":    QColor("#f97316"),
}


class HexCanvas(QWidget):
    hex_clicked = pyqtSignal(int, int)   # q, r — existing tile selected
    hex_deselected = pyqtSignal()
    hex_hovered = pyqtSignal(int, int)   # q, r

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: dict[Coord, dict] = {}
        self._selected: Coord | None = None
        self._hover: Coord | None = None
        self._offset = [0.0, 0.0]
        self._hex_size = _HEX_SIZE_DEFAULT
        self._pan_anchor: tuple[float, float, float, float] | None = None
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
        self.update()

    def apply_tile(self, q: int, r: int, data: dict) -> None:
        self._tiles[(q, r)] = data
        self.update()

    def remove_tile(self, q: int, r: int) -> None:
        self._tiles.pop((q, r), None)
        if self._selected == (q, r):
            self._selected = None
        self.update()

    def clear(self) -> None:
        self._tiles.clear()
        self._selected = None
        self._hover = None
        self.update()

    def set_selected(self, coord: Coord | None) -> None:
        self._selected = coord
        self.update()

    def clear_selection(self) -> None:
        if self._selected is None:
            return
        self._selected = None
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

        # Fill
        if structure:
            fill = _STRUCTURE_COLORS.get(structure.get("type", ""), _FILLED_FILL)
            painter.setBrush(fill if not is_hover else fill.lighter(115))
        elif is_hover:
            painter.setBrush(_HOVER_FILL)
        else:
            painter.setBrush(_EMPTY_FILL)

        # Border
        if is_selected:
            painter.setPen(QPen(_SELECTED_BORDER, 2.5))
        elif structure:
            painter.setPen(QPen(_FILLED_BORDER, 1.0))
        else:
            painter.setPen(QPen(_EMPTY_BORDER, 1.0, Qt.PenStyle.DashLine))

        painter.drawPolygon(poly)

        # Overlay tile image from asset registry when available
        if structure:
            stype = structure.get("type", "")
            tile_px = REGISTRY.pixmap(stype, self._hex_size)
            if tile_px is not None:
                size = round(self._hex_size)
                painter.drawPixmap(round(cx) - size, round(cy) - size, tile_px)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(_SELECTED_BORDER if is_selected else _FILLED_BORDER,
                                    2.5 if is_selected else 1.0))
                painter.drawPolygon(poly)

        # Road indicator — small horizontal bar
        if data.get("road"):
            road_color = QColor(data["road"].get("color", "#5ea500"))
            pen = QPen(road_color, _ROAD_WIDTH, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            hw = self._hex_size * 0.35
            painter.drawLine(QPointF(cx - hw, cy), QPointF(cx + hw, cy))

        # Description indicator — small dot bottom-right
        if data.get("description"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(_DESC_DOT_COLOR)
            r_dot = self._hex_size * 0.08
            painter.drawEllipse(QPointF(cx + self._hex_size * 0.35,
                                        cy + self._hex_size * 0.45),
                                r_dot, r_dot)

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
            hit = self._hit_test(x, y)
            if hit is None:
                if self._selected is not None:
                    self._selected = None
                    self.update()
                    self.hex_deselected.emit()
                return
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
        hit = self._hit_test(x, y)
        if self._hover != hit:
            self._hover = hit
            self.update()
            if hit is not None:
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

    def _hit_test(self, cx: float, cy: float) -> Coord | None:
        """Return the map tile under (cx, cy), or None for empty canvas / gaps.

        Unlike raw pixel_to_hex (infinite grid), only coords present in
        ``_tiles`` count — same rule as hex-mvp-recovered's ``HexState.hexes``.
        """
        if not self._tiles:
            return None
        q, r = self._canvas_to_hex(cx, cy)
        if (q, r) not in self._tiles:
            return None
        ox, oy = self._origin()
        hpx, hpy = hex_to_pixel(q, r, self._hex_size)
        dist_sq = (cx - ox - hpx) ** 2 + (cy - oy - hpy) ** 2
        if dist_sq > (self._hex_size * 0.92) ** 2:
            return None
        return (q, r)
