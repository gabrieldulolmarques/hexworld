from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent, QPen, QPixmap
from PyQt6.QtWidgets import QSizePolicy

from styles.colors import GREEN_PRIMARY_RGB, GREEN_TINT
from views.hex_canvas import HexCanvas
from views.map.constants import MINIMAP_H, SIDE_PANEL_W
from views.map.panel import MapPanel

_MINIMAP_W = SIDE_PANEL_W
_MINIMAP_H = MINIMAP_H
_MINIMAP_PAD = 14
_MINIMAP_RADIUS = 12.0
_MINIMAP_HEX_SIZE_MIN = 8.0

def _viewport_fill() -> QColor:
    r, g, b = (int(part.strip()) for part in GREEN_PRIMARY_RGB.split(","))
    return QColor(r, g, b, 56)

_VIEWPORT_FILL = _viewport_fill()
_VIEWPORT_BORDER = QColor(GREEN_TINT)

class MinimapWidget(MapPanel):
    def __init__(self, canvas: HexCanvas, parent=None) -> None:
        super().__init__("mapMinimap", parent)
        self._canvas = canvas
        self._pixmap = None
        self._map_hex_size = _MINIMAP_HEX_SIZE_MIN
        self._cached_dpr = 1.0
        self._map_min_x = 0.0
        self._map_min_y = 0.0
        self._map_w = 0.0
        self._map_h = 0.0
        self._draw_rect = QRectF()
        self._cache_dirty = True

        self.setFixedSize(_MINIMAP_W, _MINIMAP_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setToolTip("Minimap — click to recenter view")

        canvas.map_changed.connect(self._mark_dirty)
        canvas.viewport_changed.connect(self.update)

    def _mark_dirty(self) -> None:
        self._cache_dirty = True
        self.update()

    def _ensure_cache(self) -> None:
        dpr = max(1.0, self.devicePixelRatioF())
        if not self._cache_dirty and dpr == self._cached_dpr:
            return
        self._cache_dirty = False
        self._cached_dpr = dpr

        inner_w = max(1.0, self.width() - 2 * _MINIMAP_PAD)
        inner_h = max(1.0, self.height() - 2 * _MINIMAP_PAD)
        target_w = inner_w * dpr
        target_h = inner_h * dpr
        hex_size = self._canvas.minimap_hex_size_for(
            target_w,
            target_h,
            min_hex=_MINIMAP_HEX_SIZE_MIN,
        )
        self._map_hex_size = hex_size

        rendered = self._canvas.render_minimap_image(hex_size)
        if rendered is None:
            self._pixmap = None
            self._map_w = 0.0
            self._map_h = 0.0
            self._draw_rect = QRectF()
            return

        image, self._map_min_x, self._map_min_y, self._map_w, self._map_h = rendered
        self._pixmap = QPixmap.fromImage(image)

        inner_w = max(1.0, self.width() - 2 * _MINIMAP_PAD)
        inner_h = max(1.0, self.height() - 2 * _MINIMAP_PAD)
        scale = min(inner_w / self._map_w, inner_h / self._map_h)
        draw_w = self._map_w * scale
        draw_h = self._map_h * scale
        draw_x = (self.width() - draw_w) / 2
        draw_y = (self.height() - draw_h) / 2
        self._draw_rect = QRectF(draw_x, draw_y, draw_w, draw_h)

    def _content_rect(self) -> QRectF:
        inset = _MINIMAP_PAD
        return QRectF(
            inset,
            inset,
            max(1.0, self.width() - 2 * inset),
            max(1.0, self.height() - 2 * inset),
        )

    @staticmethod
    def _rounded_path(rect: QRectF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path

    def paintEvent(self, _event: QPaintEvent) -> None:
        self._ensure_cache()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setClipPath(self._rounded_path(outer, _MINIMAP_RADIUS))

        content = self._content_rect()
        inner_radius = max(4.0, _MINIMAP_RADIUS - _MINIMAP_PAD / 2)
        painter.fillPath(
            self._rounded_path(content, inner_radius),
            QColor("#141416"),
        )

        if self._pixmap is None or self._pixmap.isNull() or self._draw_rect.isEmpty():
            painter.setPen(QColor("#71717a"))
            painter.drawText(
                content.toRect(),
                int(Qt.AlignmentFlag.AlignCenter),
                "No map content",
            )
            return

        painter.setClipPath(self._rounded_path(content, inner_radius))
        target = self._draw_rect.toRect()
        painter.drawPixmap(target, self._pixmap)

        viewport = self._canvas.viewport_rect_in_map_image(
            self._map_hex_size,
            self._map_min_x,
            self._map_min_y,
        )
        if viewport.isEmpty():
            return

        scale_x = self._draw_rect.width() / self._map_w
        scale_y = self._draw_rect.height() / self._map_h
        vx = self._draw_rect.x() + viewport.x() * scale_x
        vy = self._draw_rect.y() + viewport.y() * scale_y
        vw = viewport.width() * scale_x
        vh = viewport.height() * scale_y
        view_rect = QRectF(vx, vy, vw, vh)

        painter.fillRect(view_rect, _VIEWPORT_FILL)
        pen = QPen(_VIEWPORT_BORDER, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(view_rect)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        if self._pixmap is None or self._draw_rect.isEmpty():
            return

        pos = event.position()
        if not self._draw_rect.contains(pos.x(), pos.y()):
            return

        rel_x = (pos.x() - self._draw_rect.x()) / self._draw_rect.width()
        rel_y = (pos.y() - self._draw_rect.y()) / self._draw_rect.height()
        image_x = rel_x * self._map_w
        image_y = rel_y * self._map_h
        self._canvas.pan_to_map_image_point(
            image_x,
            image_y,
            self._map_hex_size,
            self._map_min_x,
            self._map_min_y,
        )
        event.accept()
