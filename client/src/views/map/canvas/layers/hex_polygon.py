from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPolygonF

from models.geometry import hex_vertices

def make_hex_polygon(cx: float, cy: float, size: float) -> QPolygonF:
    return QPolygonF([QPointF(x, y) for x, y in hex_vertices(cx, cy, size)])
