from math import cos, radians, sin

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPaintEvent, QPixmap, QPolygonF
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QWidget

from styles.colors import GREEN_PRIMARY, GREEN_TINT

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
        _paint_hex_logo(painter, self._size)

def hex_logo_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    _paint_hex_logo(painter, size)
    painter.end()
    return pixmap

def hex_logo_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(hex_logo_pixmap(size))
    return icon

def _paint_hex_logo(painter: QPainter, size: int) -> None:
    cx = size / 2
    cy = size / 2
    outer = size / 2 - min(4, size / 4)

    outer_hex = _hexagon(cx, cy, outer)
    painter.setBrush(QColor(GREEN_PRIMARY))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(outer_hex)

    inner_hex = _hexagon(cx, cy, outer * 0.62)
    painter.setBrush(QColor("#09090b"))
    painter.drawPolygon(inner_hex)

    core_hex = _hexagon(cx, cy, outer * 0.32)
    painter.setBrush(QColor(GREEN_TINT))
    painter.drawPolygon(core_hex)

def _hexagon(cx: float, cy: float, radius: float) -> QPolygonF:

    polygon = QPolygonF()
    for i in range(6):
        angle = radians(60 * i)
        polygon.append(QPointF(cx + radius * cos(angle), cy + radius * sin(angle)))
    return polygon

def apply_panel_style(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

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
