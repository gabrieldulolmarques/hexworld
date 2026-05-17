from math import cos, radians, sin

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPolygonF
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QWidget

class StatusMixin:
    status_label: QLabel

    def show_message(self, message: str, level: str = "info") -> None:
        self.status_label.setText(message)
        self._set_status_level(level)

    def _set_status_level(self, level: str) -> None:
        self.status_label.setProperty("level", level)
        style = self.status_label.style()
        style.unpolish(self.status_label)
        style.polish(self.status_label)

class HexLogo(QWidget):
    def __init__(self, size: int = 72, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self._size / 2
        cy = self._size / 2
        outer = self._size / 2 - 4

        outer_hex = self._hexagon(cx, cy, outer)
        painter.setBrush(QColor("#5ea500"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(outer_hex)

        inner_hex = self._hexagon(cx, cy, outer * 0.62)
        painter.setBrush(QColor("#09090b"))
        painter.drawPolygon(inner_hex)

        core_hex = self._hexagon(cx, cy, outer * 0.32)
        painter.setBrush(QColor("#d8f999"))
        painter.drawPolygon(core_hex)

    @staticmethod
    def _hexagon(cx: float, cy: float, radius: float) -> QPolygonF:
        polygon = QPolygonF()
        for i in range(6):
            angle = radians(60 * i - 30)
            polygon.append(QPointF(cx + radius * cos(angle), cy + radius * sin(angle)))
        return polygon

def make_card_shadow() -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(40)
    shadow.setOffset(0, 12)
    shadow.setColor(QColor(0, 0, 0, 160))
    return shadow

def horizontal_divider() -> QFrame:
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.Shape.HLine)
    return line
