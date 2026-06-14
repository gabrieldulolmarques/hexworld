from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget

from models.geometry import Coord
from models.map.local_map_state import LocalMapState
from styles.colors import GREEN_PRIMARY
from views.map.canvas.input_handler import InputHandler
from views.map.canvas.pick_helper import PickHelper
from views.map.canvas.renderer import Renderer
from views.map.canvas.viewport import Viewport

_HEX_SIZE_MIN = 20.0
_HEX_SIZE_MAX = 80.0
_HEX_SIZE_DEFAULT = 40.0
_ZOOM_STEP = 4.0
_EXPORT_HEX_SIZE = _HEX_SIZE_MAX
_EXPORT_SCALE_MIN = 2.0

from PyQt6.QtGui import QColor

_BG = QColor("#09090b")

class MapCanvas(QWidget):
    hex_clicked = pyqtSignal(int, int)
    hex_deselected = pyqtSignal()
    hex_hovered = pyqtSignal(int, int)
    path_drawn = pyqtSignal(list, str)
    edge_painted = pyqtSignal(int, int, int, str)
    current_path_points_changed = pyqtSignal(int)
    map_changed = pyqtSignal()
    viewport_changed = pyqtSignal()

    def __init__(
        self,
        map_state: LocalMapState | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._state = map_state or LocalMapState()

        from views.map.canvas.layers.description_layer import DescriptionLayer
        from views.map.canvas.layers.edge_layer import EdgeLayer
        from views.map.canvas.layers.hint_layer import HintLayer
        from views.map.canvas.layers.path_layer import PathLayer
        from views.map.canvas.layers.tile_layer import TileLayer

        self._tile_layer = TileLayer()
        self._path_layer = PathLayer()
        self._edge_layer = EdgeLayer()
        self._hint_layer = HintLayer()
        self._description_layer = DescriptionLayer()

        self._selected: Coord | None = None
        self._hover: Coord | None = None
        self._hover_component: str | None = None
        self._hover_path_id: str | None = None
        self._offset = [0.0, 0.0]
        self._hex_size = _HEX_SIZE_DEFAULT
        self._pan_anchor: tuple[float, float, float, float] | None = None
        self._pan_mode = False
        self._pick_any_hex = False
        self._erase_mode = False
        self._brush_mode = False
        self._brush_active = False
        self._brush_seen_targets: set[tuple] = set()

        self._path_mode = False
        self._path_color = GREEN_PRIMARY
        self._path_submode = "path"
        self._current_path: list[Coord] = []

        self._hover_edge: tuple[Coord, int] | None = None

        # path_hint_next cache — recomputed only when _current_path changes
        self._path_hint_cache: set[Coord] = set()
        self._path_hint_dirty: bool = True

        self._pick = PickHelper(self)
        self._input = InputHandler(self, self._pick)
        self._viewport = Viewport(self)
        self._renderer = Renderer(self)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(400, 300)

    # ----------------------------------------------------------------- notify

    def notify_state_changed(self) -> None:
        self.update()
        self.map_changed.emit()

    def notify_tile_removed(self, q: int, r: int) -> None:
        if self._selected == (q, r):
            self._selected = None
        if self._hover == (q, r):
            self._hover = None
            self._hover_component = None
        self.update()
        self.map_changed.emit()

    def notify_map_replaced(self) -> None:
        self._selected = None
        self._hover = None
        self._hover_component = None
        self._hover_path_id = None
        self._hover_edge = None
        self._clear_current_path(emit=False)
        self.update()
        self.map_changed.emit()

    def clear(self) -> None:
        self._clear_current_path(emit=False)
        self._selected = None
        self._hover = None
        self._hover_component = None
        self._hover_path_id = None
        self._hover_edge = None
        self.update()
        self.map_changed.emit()

    def clear_selection(self) -> None:
        if self._selected is None:
            return
        self._selected = None
        self.update()

    # ------------------------------------------------------------------ modes

    def set_erase_mode(self, enabled: bool) -> None:
        self._erase_mode = enabled
        if not enabled:
            self._hover_component = None
            self._hover_path_id = None
            self._brush_active = False
            self._brush_seen_targets.clear()
        self.update()

    def set_brush_mode(self, enabled: bool) -> None:
        self._brush_mode = enabled
        if not enabled:
            self._brush_active = False
            self._brush_seen_targets.clear()

    def set_pan_mode(self, enabled: bool) -> None:
        self._pan_mode = enabled
        if enabled:
            self._hover = None
            self._hover_component = None
            self._hover_path_id = None
            self._hover_edge = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self._pan_anchor is None and not self._path_mode:
            self.unsetCursor()
        self.update()

    def set_pick_any_hex(self, enabled: bool) -> None:
        self._pick_any_hex = enabled
        if (
            not enabled
            and self._hover is not None
            and self._hover not in self._state.tiles
        ):
            self._hover = None
            self._hover_component = None
            self.update()

    def set_path_mode(self, enabled: bool, color: str = "") -> None:
        self._path_mode = enabled
        self._path_hint_dirty = True
        if color:
            self._path_color = color
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
            self._clear_current_path()
            self._hover_edge = None
        self.update()

    def set_path_submode(self, submode: str) -> None:
        if submode not in ("path", "edge"):
            return
        self._path_submode = submode
        self._path_hint_dirty = True
        if submode != "edge":
            self._hover_edge = None
        self.update()

    def set_path_color(self, color: str) -> None:
        self._path_color = color

    # --------------------------------------------------------------- path ops

    def undo_current_path_point(self) -> None:
        if not self._current_path:
            return
        self._current_path.pop()
        self.current_path_points_changed.emit(len(self._current_path))
        self.update()

    def finish_current_path(self) -> None:
        if len(self._current_path) < 2:
            return
        waypoints = [[q, r] for q, r in self._current_path]
        color = self._path_color
        self._clear_current_path()
        self.path_drawn.emit(waypoints, color)

    def cancel_current_path(self) -> None:
        self._clear_current_path()

    def _clear_current_path(self, *, emit: bool = True) -> None:
        if not self._current_path and emit:
            self.current_path_points_changed.emit(0)
            return
        self._current_path = []
        self._path_hint_dirty = True
        if emit:
            self.current_path_points_changed.emit(0)
        self.update()

    # --------------------------------------------------------------- accessors

    def hovered_erase_component(self) -> str | None:
        return self._hover_component

    def hovered_coord(self) -> Coord | None:
        return self._hover

    def hovered_path_id(self) -> str | None:
        return self._hover_path_id

    def hovered_edge(self) -> tuple[Coord, int] | None:
        return self._hover_edge

    # --------------------------------------------------------------- zoom/pan

    def zoom_in(self) -> None:
        self._viewport.zoom_in()

    def zoom_out(self) -> None:
        self._viewport.zoom_out()

    def _emit_viewport_changed(self) -> None:
        self._viewport.emit_changed()

    def _origin(
        self,
        *,
        width: float | None = None,
        height: float | None = None,
    ) -> tuple[float, float]:
        return self._viewport.origin(width=width, height=height)

    # ---------------------------------------------------------------- events

    def wheelEvent(self, event) -> None:
        self._input.wheel(event)

    def mousePressEvent(self, event) -> None:
        if not self._input.mouse_press(event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        self._input.mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if not self._input.mouse_release(event):
            super().mouseReleaseEvent(event)

    def leaveEvent(self, _event) -> None:
        self._input.leave()

    def keyPressEvent(self, event) -> None:
        if not self._input.key_press(event):
            super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._emit_viewport_changed()

    # --------------------------------------------------------------- painting

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        self._renderer.paint(painter)

    # --------------------------------------------------------------- export / minimap (delegated)

    def export_full_map_image(self) -> QImage:
        return self._renderer.export_full_map_image()

    def minimap_hex_size_for(
        self,
        target_w: float,
        target_h: float,
        *,
        min_hex: float = 8.0,
    ) -> float:
        return self._renderer.minimap_hex_size_for(target_w, target_h, min_hex=min_hex)

    def render_minimap_image(
        self,
        hex_size: float = 8.0,
    ) -> tuple[QImage, float, float, float, float] | None:
        return self._renderer.render_minimap_image(hex_size)

    def viewport_rect_in_map_image(
        self,
        map_hex_size: float,
        map_min_x: float,
        map_min_y: float,
    ) -> QRectF:
        return self._renderer.viewport_rect_in_map_image(map_hex_size, map_min_x, map_min_y)

    def pan_to_map_image_point(
        self,
        image_x: float,
        image_y: float,
        map_hex_size: float,
        map_min_x: float,
        map_min_y: float,
    ) -> None:
        self._renderer.pan_to_map_image_point(image_x, image_y, map_hex_size, map_min_x, map_min_y)
