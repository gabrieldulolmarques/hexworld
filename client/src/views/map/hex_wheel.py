"""Hex color wheel used by the road-color picker."""

import math

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget


class HexWheel(QWidget):
    """Hex color wheel matching the reference image style."""

    color_picked = pyqtSignal(str)

    _RADIUS = 5
    _CELL = 15   # pixel radius of each hex cell

    def __init__(self) -> None:
        super().__init__()
        self._selected: tuple[int, int] | None = None
        self._hovered:  tuple[int, int] | None = None
        self._cells: list[tuple[int, int, QColor]] = self._build()
        # flat-top hex grid bounding box:  w = s*(3R+2),  h = sqrt(3)*s*(2R+1)
        w = int(self._CELL * (3 * self._RADIUS + 2)) + 8
        h = int(math.sqrt(3) * self._CELL * (2 * self._RADIUS + 1)) + 8
        self.setFixedSize(w, h)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _build(self) -> list[tuple[int, int, QColor]]:
        R = self._RADIUS
        cells = []
        for q in range(-R, R + 1):
            r_lo = max(-R, -q - R)
            r_hi = min(R, -q + R)
            for r in range(r_lo, r_hi + 1):
                d = max(abs(q), abs(r), abs(-q - r))
                if d == 0:
                    color = QColor("#ffffff")
                else:
                    # flat-top layout angle (hue mapping)
                    x = q * 1.5
                    y = math.sqrt(3) * (r + q * 0.5)
                    angle = math.degrees(math.atan2(y, x)) % 360
                    norm = d / R
                    if norm <= 0.35:
                        sat = norm / 0.35 * 0.45
                        val = 1.0
                    elif norm <= 0.7:
                        t = (norm - 0.35) / 0.35
                        sat = 0.45 + t * 0.55
                        val = 1.0
                    else:
                        t = (norm - 0.7) / 0.3
                        sat = 1.0
                        val = 1.0 - t * 0.65
                    color = QColor.fromHsvF(angle / 360, min(1.0, sat), max(0.2, val))
                cells.append((q, r, color))
        return cells

    def _center(self, q: int, r: int) -> QPointF:
        # flat-top layout: x = 1.5*s*q,  y = sqrt(3)*s*(r + q/2)
        s = self._CELL
        cx = self.width() / 2
        cy = self.height() / 2
        return QPointF(
            cx + s * 1.5 * q,
            cy + s * math.sqrt(3) * (r + q * 0.5),
        )

    def _polygon(self, cx: float, cy: float) -> QPolygonF:
        # flat-top cell: offset 0° → flat edge at top/bottom, vertex at sides
        s = self._CELL - 1.0
        pts = [
            QPointF(cx + s * math.cos(math.radians(60 * i)),
                    cy + s * math.sin(math.radians(60 * i)))
            for i in range(6)
        ]
        return QPolygonF(pts)

    def _cell_at(self, pos: QPointF) -> tuple[int, int] | None:
        best, best_d = None, (self._CELL * 1.1) ** 2
        for q, r, _ in self._cells:
            c = self._center(q, r)
            d = (c.x() - pos.x()) ** 2 + (c.y() - pos.y()) ** 2
            if d < best_d:
                best_d, best = d, (q, r)
        return best

    def _color_at(self, qr: tuple[int, int]) -> QColor | None:
        for q, r, color in self._cells:
            if (q, r) == qr:
                return color
        return None

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for q, r, color in self._cells:
            c = self._center(q, r)
            poly = self._polygon(c.x(), c.y())
            p.setBrush(color)
            is_sel = self._selected == (q, r)
            is_hov = self._hovered == (q, r)
            if is_sel:
                p.setPen(QPen(QColor("#ffffff"), 2.0))
            elif is_hov:
                p.setPen(QPen(QColor("#e4e4e7"), 1.2))
            else:
                p.setPen(QPen(QColor("#09090b"), 0.5))
            p.drawPolygon(poly)

    def mouseMoveEvent(self, e) -> None:
        cell = self._cell_at(e.position())
        if cell != self._hovered:
            self._hovered = cell
            self.update()

    def leaveEvent(self, _e) -> None:
        self._hovered = None
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() != Qt.MouseButton.LeftButton:
            return
        cell = self._cell_at(e.position())
        if cell:
            self._selected = cell
            self.update()
            color = self._color_at(cell)
            if color:
                self.color_picked.emit(color.name())

    def select_color(self, hex_str: str) -> None:
        """Highlight the cell closest to the given hex color."""
        target = QColor(hex_str)
        if not target.isValid():
            return
        best, best_d = None, float("inf")
        for q, r, color in self._cells:
            dr = target.red() - color.red()
            dg = target.green() - color.green()
            db = target.blue() - color.blue()
            d = dr * dr + dg * dg + db * db
            if d < best_d:
                best_d, best = d, (q, r)
        self._selected = best
        self.update()
