from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen

_OUTLINE_FALLBACK = QColor("#18181b")

@dataclass
class PathStyle:
    kind: str = "road"
    color: str = "#5ea500"

def road_style(color: str) -> PathStyle:
    return PathStyle(kind="road", color=color)

def _stroke_widths(hex_size: float) -> tuple[int, int]:
    outline_w = max(2, round(hex_size * 0.14))
    fill_w = max(1, round(hex_size * 0.09))
    return outline_w, fill_w

def _outline_color(fill: QColor) -> QColor:
    h, s, v, a = fill.getHsv()
    if s < 20:
        return _OUTLINE_FALLBACK
    return QColor.fromHsv(h, min(255, s + 40), max(0, v - 50), a)

def _road_pen(color: QColor, width: int, *, preview: bool = False) -> QPen:
    pen = QPen(
        color,
        width,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    if preview:
        pen.setStyle(Qt.PenStyle.DashLine)
    return pen

def _draw_road_path(
    painter: QPainter,
    path: QPainterPath,
    hex_size: float,
    style: PathStyle,
    *,
    preview: bool,
    highlight: bool,
) -> None:
    outline_w, fill_w = _stroke_widths(hex_size)

    fill_color = QColor(style.color)
    if preview:
        fill_color.setAlphaF(0.65)
    if highlight:
        fill_color = QColor("#ef4444")

    outline_color = _outline_color(fill_color) if not highlight else fill_color

    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(_road_pen(outline_color, outline_w, preview=preview))
    painter.drawPath(path)
    painter.setPen(_road_pen(fill_color, fill_w, preview=preview))
    painter.drawPath(path)

def paint_pixel_segments(
    painter: QPainter,
    origin: tuple[float, float],
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    hex_size: float,
    style: PathStyle,
    *,
    preview: bool = False,
    highlight: bool = False,
) -> None:
    if not segments:
        return

    ox, oy = origin
    path = QPainterPath()
    for (start_x, start_y), (end_x, end_y) in segments:
        path.moveTo(QPointF(ox + start_x, oy + start_y))
        path.lineTo(QPointF(ox + end_x, oy + end_y))

    _draw_road_path(
        painter, path, hex_size, style,
        preview=preview, highlight=highlight,
    )
