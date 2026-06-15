from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen

from models.geometry import Coord, hex_to_pixel
from styles.colors import GREEN_PRIMARY_RGB, GREEN_TINT
from views.map.canvas.layers.hex_polygon import make_hex_polygon
from views.map.canvas.layers.colors import rgba_color
from views.map.canvas.layers.paint_context import PaintContext

_PATH_HINT_FILL = rgba_color(GREEN_PRIMARY_RGB, 42)
_PATH_HINT_BORDER = QColor(GREEN_TINT)
_PATH_NEXT_FILL = rgba_color(GREEN_PRIMARY_RGB, 22)

class HintLayer:
    def paint(self, ctx: PaintContext) -> None:
        if not ctx.include_transient:
            return
        if not (ctx.path_mode and ctx.path_submode == "path"):
            return

        current = set(ctx.current_path or ())
        next_coords = ctx.path_hint_next_hexes or set()

        for coord in current:
            self._draw_hint_hex(
                ctx,
                coord,
                fill=_PATH_HINT_FILL,
                pen=QPen(_PATH_HINT_BORDER, 2.4),
            )
        for coord in next_coords - current:
            self._draw_hint_hex(
                ctx,
                coord,
                fill=_PATH_NEXT_FILL,
                pen=QPen(_PATH_HINT_BORDER, 1.4, Qt.PenStyle.DashLine),
            )

    @staticmethod
    def _draw_hint_hex(
        ctx: PaintContext,
        coord: Coord,
        *,
        fill: QColor,
        pen: QPen,
    ) -> None:
        ox, oy = ctx.origin
        px, py = hex_to_pixel(coord[0], coord[1], ctx.hex_size)
        poly = make_hex_polygon(ox + px, oy + py, ctx.hex_size - 1.5)
        ctx.painter.setBrush(fill)
        ctx.painter.setPen(pen)
        ctx.painter.drawPolygon(poly)
