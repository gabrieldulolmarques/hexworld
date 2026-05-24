"""Path (road / future river / border) rendering styles for HexCanvas."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen

from geometry import path_pixel_points

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


def _to_canvas_points(
    origin: tuple[float, float],
    waypoints: list,
    hex_size: float,
) -> list[QPointF]:
    ox, oy = origin
    return [
        QPointF(ox + x, oy + y)
        for x, y in path_pixel_points(waypoints, hex_size)
    ]


def _build_path(pts: list[QPointF], curve: float) -> QPainterPath:
    """Build the JSX smoothPath equivalent as a QPainterPath."""
    path = QPainterPath()
    path.moveTo(pts[0])
    n = len(pts)
    if n < 2:
        return path
    if n == 2 or curve <= 0.05:
        path.lineTo(pts[-1])
        return path

    for i in range(1, n):
        if i >= n - 1:
            break
        current = pts[i]
        next_pt = pts[i + 1]
        midpoint = QPointF(
            current.x() + (next_pt.x() - current.x()) * 0.5,
            current.y() + (next_pt.y() - current.y()) * 0.5,
        )
        path.quadTo(current, midpoint)

    path.quadTo(_smooth_control_for_last(pts), pts[-1])
    return path


def _smooth_control_for_last(pts: list[QPointF]) -> QPointF:
    previous_control = pts[-2]
    last_midpoint = QPointF(
        previous_control.x() + (pts[-1].x() - previous_control.x()) * 0.5,
        previous_control.y() + (pts[-1].y() - previous_control.y()) * 0.5,
    )
    return QPointF(
        last_midpoint.x() * 2.0 - previous_control.x(),
        last_midpoint.y() * 2.0 - previous_control.y(),
    )


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


def paint_path(
    painter: QPainter,
    origin: tuple[float, float],
    waypoints: list,
    hex_size: float,
    style: PathStyle,
    *,
    curve: float = 1.0,
    preview: bool = False,
    highlight: bool = False,
) -> None:
    """Draw a road path with outline + fill; optional preview/highlight styling."""
    if len(waypoints) < 2:
        return

    pts = _to_canvas_points(origin, waypoints, hex_size)
    if len(pts) < 2:
        return

    path = _build_path(pts, curve)
    _draw_road_path(
        painter, path, hex_size, style,
        preview=preview, highlight=highlight,
    )


def paint_pixel_polyline(
    painter: QPainter,
    origin: tuple[float, float],
    points: list[tuple[float, float]],
    hex_size: float,
    style: PathStyle,
    *,
    preview: bool = False,
    highlight: bool = False,
) -> None:
    """Draw an already-sampled local pixel polyline with the road style."""
    if len(points) < 2:
        return

    ox, oy = origin
    path = QPainterPath()
    first_x, first_y = points[0]
    path.moveTo(QPointF(ox + first_x, oy + first_y))
    for x, y in points[1:]:
        path.lineTo(QPointF(ox + x, oy + y))

    _draw_road_path(
        painter, path, hex_size, style,
        preview=preview, highlight=highlight,
    )


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
    """Draw multiple local pixel segments as one road layer."""
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
