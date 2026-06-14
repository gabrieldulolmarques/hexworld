from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPen

from models.geometry import hex_to_pixel, hex_vertices
from models.path_constants import DEFAULT_PATH_COLOR
from styles.colors import RED_PRIMARY
from views.map.canvas.layers.paint_context import PaintContext

_EDGE_INSET_RATIO = 0.84
_ERASE_HOVER_BORDER = QColor(RED_PRIMARY)

def edge_size(hex_size: float) -> float:
    return max(1.0, hex_size * _EDGE_INSET_RATIO)

class EdgeLayer:
    def paint(self, ctx: PaintContext) -> None:
        for (q, r), data in ctx.edges.items():
            edges = int(data.get("edges", 0))
            color = QColor(data.get("color", DEFAULT_PATH_COLOR))
            for edge_index in range(6):
                if edges & (1 << edge_index):
                    self._draw_edge(
                        ctx,
                        q,
                        r,
                        edge_index,
                        color,
                        active=True,
                    )

        if not ctx.include_transient:
            return

        if ctx.path_mode and ctx.path_submode == "edge" and ctx.hover_edge is not None:
            coord, edge_index = ctx.hover_edge
            self._draw_edge(
                ctx,
                coord[0],
                coord[1],
                edge_index,
                QColor(ctx.path_color),
                active=False,
            )
        elif ctx.erase_mode and ctx.hover_component == "edge" and ctx.hover_edge:
            coord, edge_index = ctx.hover_edge
            self._draw_edge(
                ctx,
                coord[0],
                coord[1],
                edge_index,
                _ERASE_HOVER_BORDER,
                active=False,
            )

    @staticmethod
    def _draw_edge(
        ctx: PaintContext,
        q: int,
        r: int,
        edge_index: int,
        color: QColor,
        *,
        active: bool,
    ) -> None:
        ox, oy = ctx.origin
        px, py = hex_to_pixel(q, r, ctx.hex_size)
        vertices = hex_vertices(ox + px, oy + py, edge_size(ctx.hex_size))
        p1 = vertices[edge_index]
        p2 = vertices[(edge_index + 1) % 6]
        pen_color = QColor(color)
        if not active:
            pen_color.setAlphaF(0.82)
        ctx.painter.setBrush(Qt.BrushStyle.NoBrush)
        ctx.painter.setPen(
            QPen(
                pen_color,
                max(2, round(ctx.hex_size * (0.09 if active else 0.075))),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        ctx.painter.drawLine(QPointF(*p1), QPointF(*p2))
