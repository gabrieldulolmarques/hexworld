from PyQt6.QtCore import QTimer

class Viewport:
    def __init__(self, canvas) -> None:
        self._canvas = canvas
        self._pending = False

    def origin(
        self,
        *,
        width: float | None = None,
        height: float | None = None,
    ) -> tuple[float, float]:
        c = self._canvas
        w = c.width() if width is None else width
        h = c.height() if height is None else height
        return (w / 2 + c._offset[0], h / 2 + c._offset[1])

    def zoom_in(self) -> None:
        from views.map.canvas.map_canvas import _HEX_SIZE_MAX, _ZOOM_STEP

        c = self._canvas
        c._hex_size = min(_HEX_SIZE_MAX, c._hex_size + _ZOOM_STEP)
        self.emit_changed()
        c.update()

    def zoom_out(self) -> None:
        from views.map.canvas.map_canvas import _HEX_SIZE_MIN, _ZOOM_STEP

        c = self._canvas
        c._hex_size = max(_HEX_SIZE_MIN, c._hex_size - _ZOOM_STEP)
        self.emit_changed()
        c.update()

    def emit_changed(self) -> None:
        if not self._pending:
            self._pending = True
            QTimer.singleShot(0, self._flush)

    def _flush(self) -> None:
        self._pending = False
        self._canvas.viewport_changed.emit()
