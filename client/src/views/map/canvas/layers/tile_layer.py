from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from models.asset_registry import REGISTRY
from models.geometry import hex_to_pixel
from styles.colors import (
    GREEN_CANVAS_FILL,
    GREEN_PRIMARY_RGB,
    GREEN_TINT,
    RED_PRIMARY,
    RED_PRIMARY_RGB,
)
from views.map.canvas.layers.colors import rgba_color
from views.map.canvas.layers.hex_polygon import make_hex_polygon
from views.map.canvas.layers.paint_context import PaintContext

_EMPTY_FILL = QColor("#18181b")
_EMPTY_BORDER = QColor("#3f3f46")
_FILLED_FILL = QColor(GREEN_CANVAS_FILL)
_FILLED_BORDER = QColor("#3f3f46")
_HOVER_FILL = rgba_color(GREEN_PRIMARY_RGB, 38)
_HOVER_BORDER = QColor(GREEN_TINT)
_ERASE_HEX_FILL = rgba_color(RED_PRIMARY_RGB, 100)
_ERASE_HOVER_BORDER = QColor(RED_PRIMARY)
_SELECTED_BORDER = QColor(GREEN_TINT)

_TERRAIN_COLORS: dict[str, QColor] = {
    "castle": QColor("#8b5cf6"),
    "village": QColor("#f59e0b"),
    "fortress": QColor("#ef4444"),
    "ruins": QColor("#6b7280"),
    "port": QColor("#3b82f6"),
    "tower": QColor("#f97316"),
}

_BIOME_COLORS: dict[str, QColor] = {
    "deadlands": QColor("#4f5346"),
    "drylands": QColor("#a8866d"),
    "forest": QColor("#498b54"),
    "greenlands": QColor("#8ab55d"),
    "icelands": QColor("#ccd8db"),
    "mountain": QColor("#6f5c5c"),
    "sandlands": QColor("#efd98d"),
}

class TileLayer:
    def paint(self, ctx: PaintContext) -> None:
        for (q, r), data in ctx.tiles.items():
            self._draw_hex(ctx, q, r, data, overlay=False)

        for q, r in ctx.extra_hexes:
            if (q, r) not in ctx.tiles:
                self._draw_hex(ctx, q, r, {}, overlay=False)

        if ctx.minimap:
            return

        for (q, r), data in ctx.tiles.items():
            self._draw_hex(ctx, q, r, data, overlay=True)

        for q, r in ctx.extra_hexes:
            if (q, r) not in ctx.tiles:
                self._draw_hex(ctx, q, r, {}, overlay=True)

        self._draw_highlights(ctx)

    def _draw_hex(
        self, ctx: PaintContext, q: int, r: int, data: dict, *, overlay: bool
    ) -> None:
        ox, oy = ctx.origin
        px, py = hex_to_pixel(q, r, ctx.hex_size)
        cx, cy = ox + px, oy + py
        poly = make_hex_polygon(cx, cy, ctx.hex_size - 1.5)
        terrain = data.get("terrain")

        if not overlay:
            self._draw_fill(ctx.painter, poly, terrain, minimap=ctx.minimap)
            return

        self._draw_overlay(ctx.painter, cx, cy, terrain, ctx.hex_size)

    @staticmethod
    def _draw_fill(
        painter: QPainter,
        poly,
        terrain: dict | None,
        *,
        minimap: bool,
    ) -> None:
        if terrain:
            painter.setBrush(TileLayer._terrain_fill_color(terrain, minimap=minimap))
        else:
            painter.setBrush(_EMPTY_FILL)

        if terrain:
            painter.setPen(QPen(_FILLED_BORDER, 1.0))
        else:
            painter.setPen(QPen(_EMPTY_BORDER, 1.0, Qt.PenStyle.DashLine))

        painter.drawPolygon(poly)

    @staticmethod
    def _terrain_fill_color(terrain: dict, *, minimap: bool) -> QColor:
        stype = terrain.get("type", "")
        if minimap:
            info = REGISTRY.tile(stype)
            if info is not None:
                return _BIOME_COLORS.get(info.biome, _FILLED_FILL)
            return _FILLED_FILL
        return _TERRAIN_COLORS.get(stype, _FILLED_FILL)

    @staticmethod
    def _draw_overlay(
        painter: QPainter,
        cx: float,
        cy: float,
        terrain: dict | None,
        hex_size: float,
    ) -> None:
        if not terrain:
            return
        stype = terrain.get("type", "")
        tile_px = REGISTRY.pixmap(stype, hex_size)
        if tile_px is not None:
            size = round(hex_size)
            painter.drawPixmap(round(cx) - size, round(cy) - size, tile_px)

    def _draw_highlights(self, ctx: PaintContext) -> None:
        if not ctx.include_transient:
            return

        ox, oy = ctx.origin
        coords = set(ctx.tiles.keys())
        coords.update(ctx.extra_hexes)

        for q, r in coords:
            is_selected = ctx.selected == (q, r)
            is_hover = ctx.hover == (q, r)
            if not is_selected and not is_hover:
                continue

            erase_comp = ctx.hover_component if is_hover and ctx.erase_mode else None
            px, py = hex_to_pixel(q, r, ctx.hex_size)
            poly = make_hex_polygon(ox + px, oy + py, ctx.hex_size - 1.5)

            if is_hover and ctx.erase_mode and erase_comp == "terrain":
                ctx.painter.setBrush(_ERASE_HEX_FILL)
                ctx.painter.setPen(QPen(_ERASE_HOVER_BORDER, 2.5))
                ctx.painter.drawPolygon(poly)
            elif is_selected:
                ctx.painter.setBrush(Qt.BrushStyle.NoBrush)
                ctx.painter.setPen(QPen(_SELECTED_BORDER, 2.5))
                ctx.painter.drawPolygon(poly)
            elif is_hover and not ctx.erase_mode:
                ctx.painter.setBrush(_HOVER_FILL)
                ctx.painter.setPen(QPen(_HOVER_BORDER, 2.0))
                ctx.painter.drawPolygon(poly)
