from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from models.geometry import hex_to_pixel
from resources import assets_path
from styles.colors import RED_PRIMARY
from views.map.canvas.layers.paint_context import PaintContext

_ICONS_DIR = assets_path("icons")
_DESC_ICON_CACHE: dict[tuple[int, str], QPixmap] = {}

_ERASE_HOVER_BORDER = QColor(RED_PRIMARY)
_DESC_BADGE_FILL = QColor("#facc15")
_DESC_BADGE_BORDER = QColor("#18181b")
_DESC_BADGE_ICON = QColor("#18181b")
_DESC_BADGE_SHADOW = QColor(0, 0, 0, 150)
_DESC_ERASE_ICON = QColor("#fff7ed")

def description_badge_center(
    origin: tuple[float, float],
    q: int,
    r: int,
    hex_size: float,
) -> tuple[float, float]:
    ox, oy = origin
    px, py = hex_to_pixel(q, r, hex_size)
    return (
        ox + px + hex_size * 0.38,
        oy + py + hex_size * 0.43,
    )

def _desc_icon(size: int, color: QColor) -> QPixmap:
    key = (size, color.name())
    if key not in _DESC_ICON_CACHE:
        raw = QIcon(str(_ICONS_DIR / "scroll-text.svg")).pixmap(QSize(size, size))
        if raw.isNull():
            _DESC_ICON_CACHE[key] = raw
            return raw
        tinted = QPixmap(raw.size())
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.drawPixmap(0, 0, raw)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), color)
        p.end()
        _DESC_ICON_CACHE[key] = tinted
    return _DESC_ICON_CACHE[key]

class DescriptionLayer:
    def paint(self, ctx: PaintContext) -> None:
        if ctx.minimap:
            return

        for (q, r), data in ctx.tiles.items():
            if not data.get("description"):
                continue
            is_hover = ctx.include_transient and ctx.hover == (q, r)
            active = (
                ctx.include_transient
                and is_hover
                and ctx.erase_mode
                and ctx.hover_component == "description"
            )
            self._draw_badge(ctx, q, r, active=active)

    @staticmethod
    def _draw_badge(ctx: PaintContext, q: int, r: int, *, active: bool) -> None:
        cx, cy = description_badge_center(ctx.origin, q, r, ctx.hex_size)
        radius = max(8.0, ctx.hex_size * 0.17)
        fill = _ERASE_HOVER_BORDER if active else _DESC_BADGE_FILL
        border = _DESC_ERASE_ICON if active else _DESC_BADGE_BORDER
        icon_color = _DESC_ERASE_ICON if active else _DESC_BADGE_ICON

        ctx.painter.setPen(Qt.PenStyle.NoPen)
        ctx.painter.setBrush(_DESC_BADGE_SHADOW)
        ctx.painter.drawEllipse(QPointF(cx + 1.5, cy + 2.0), radius, radius)

        ctx.painter.setBrush(fill)
        ctx.painter.setPen(QPen(border, max(1.4, ctx.hex_size * 0.035)))
        ctx.painter.drawEllipse(QPointF(cx, cy), radius, radius)

        icon_size = max(11, round(radius * 1.18))
        icon = _desc_icon(icon_size, icon_color)
        if not icon.isNull():
            ctx.painter.drawPixmap(
                round(cx) - icon_size // 2,
                round(cy) - icon_size // 2,
                icon,
            )
