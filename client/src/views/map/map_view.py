from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QKeySequence, QShortcut
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from views.map.canvas.map_canvas import MapCanvas
from models.map.local_map_state import LocalMapState
from views.map.widgets.map_body import MapBody
from models.map.tool_ids import (
    TOOL_DESCRIPTION,
    TOOL_ERASE,
    TOOL_PAN,
    TOOL_PATH,
    TOOL_SELECT,
    TOOL_TERRAIN,
)
from views.map.widgets.description_editor import DescriptionEditor
from views.map.widgets.export_dialog import ExportDialog
from views.map.widgets.members_bar import MembersBar
from views.map.widgets.minimap import MinimapWidget
from views.map.widgets.palette_panel import PalettePanel
from views.map.widgets.map_panel import styled
from views.map.widgets.path_panel import PathColorPanel
from views.map.widgets.select_panel import SelectPanel
from views.map.widgets.tool_strip import ToolStrip
from views.map.widgets.map_toolbar import MapToolbar

class MapView(QWidget):
    back_requested = pyqtSignal()
    hex_selected = pyqtSignal(int, int)
    hex_paint_clicked = pyqtSignal(int, int)
    terrain_selected = pyqtSignal(str)
    path_color_selected = pyqtSignal(str)
    path_drawn = pyqtSignal(list, str)
    edge_painted = pyqtSignal(int, int, int, str)
    tool_changed = pyqtSignal(str)
    description_submitted = pyqtSignal(int, int, str)
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    export_requested = pyqtSignal()
    export_submitted = pyqtSignal(str)

    def __init__(self, map_state: LocalMapState | None = None) -> None:
        super().__init__()
        self.setObjectName("mapScreen")
        styled(self)
        self._active_tool = TOOL_SELECT
        self._state = map_state or LocalMapState()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.canvas = MapCanvas(self._state)
        self.canvas.setObjectName("mapCanvas")
        self.canvas.hex_clicked.connect(self._on_hex_clicked)
        self.canvas.hex_deselected.connect(self._on_hex_deselected)

        self._toolbar = MapToolbar()
        self._select_panel = SelectPanel()
        self._members_bar = MembersBar()
        self._tool_strip = ToolStrip()
        self._palette = PalettePanel()
        self._path_panel = PathColorPanel()
        self._description_editor = DescriptionEditor()
        self._export_dialog = ExportDialog()
        self._minimap = MinimapWidget(self.canvas)

        self._members_bar.connect_back(self.back_requested)
        self._palette.terrain_selected.connect(self.terrain_selected)
        self._path_panel.path_color_selected.connect(self.path_color_selected)
        self._path_panel.path_color_selected.connect(self.canvas.set_path_color)
        self._path_panel.path_submode_changed.connect(self._on_path_submode_changed)
        self.canvas.path_drawn.connect(self.path_drawn)
        self.canvas.edge_painted.connect(self.edge_painted)
        self._tool_strip.tool_changed.connect(self._on_tool_changed)
        self._tool_strip.zoom_in_clicked.connect(self._on_zoom_in)
        self._tool_strip.zoom_out_clicked.connect(self._on_zoom_out)
        self._tool_strip.undo_clicked.connect(self.undo_requested)
        self._tool_strip.redo_clicked.connect(self.redo_requested)
        self._tool_strip.export_clicked.connect(self.export_requested)
        self._description_editor.submitted.connect(self.description_submitted)
        self._export_dialog.submitted.connect(self.export_submitted)
        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self.canvas)
        self._undo_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._undo_shortcut.activated.connect(self.undo_requested)
        self._redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self.canvas)
        self._redo_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._redo_shortcut.activated.connect(self.redo_requested)

        self._body = MapBody(
            self.canvas,
            self._toolbar,
            self._select_panel,
            self._members_bar,
            self._tool_strip,
            self._palette,
            self._path_panel,
            self._description_editor,
            self._export_dialog,
            self._minimap,
        )

        self._error_banner = QLabel()
        self._error_banner.setObjectName("mapErrorBanner")
        self._error_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_banner.setWordWrap(False)
        self._error_banner.setMinimumHeight(44)
        self._error_banner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._error_banner.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._error_banner.hide()
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(self._error_banner.hide)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._error_banner)
        root.addWidget(self._body, 1)
        self._body.sync_panels(TOOL_SELECT)

    def _on_hex_clicked(self, q: int, r: int) -> None:
        self._select_panel.set_coord(q, r)
        if self._active_tool == TOOL_SELECT:
            self.refresh_inspector(q, r)
            self.hex_selected.emit(q, r)
            self._body.sync_panels(TOOL_SELECT)
        elif self._active_tool in (TOOL_TERRAIN, TOOL_DESCRIPTION, TOOL_ERASE):

            self.hex_paint_clicked.emit(q, r)

    def _on_hex_deselected(self) -> None:
        self._select_panel.clear_selection()
        if self._active_tool == TOOL_SELECT:
            self._body.sync_panels(TOOL_SELECT)

    def _apply_canvas_tool(self, tool_id: str) -> None:
        self.canvas.set_pick_any_hex(
            tool_id in (TOOL_TERRAIN, TOOL_DESCRIPTION, TOOL_PATH)
        )
        self.canvas.set_erase_mode(tool_id == TOOL_ERASE)
        self.canvas.set_brush_mode(tool_id in (TOOL_TERRAIN, TOOL_ERASE))
        self.canvas.set_pan_mode(tool_id == TOOL_PAN)
        self.canvas.set_path_mode(
            tool_id == TOOL_PATH, self._path_panel.selected_color()
        )
        if tool_id == TOOL_PATH:
            self.canvas.set_path_submode(self._path_panel.selected_submode())

    def _on_tool_changed(self, tool_id: str) -> None:
        if tool_id != TOOL_SELECT:
            self._select_panel.clear_selection()
            self.canvas.clear_selection()
        self._active_tool = tool_id
        self._palette.apply_tool(tool_id)
        self._body.sync_panels(tool_id)
        self._apply_canvas_tool(tool_id)
        self.tool_changed.emit(tool_id)

    def _on_path_submode_changed(self, submode: str) -> None:
        self.canvas.set_path_submode(submode)
        self._body.reposition_panels()

    def _on_zoom_in(self) -> None:
        self.canvas.zoom_in()
        self.zoom_in_requested.emit()

    def _on_zoom_out(self) -> None:
        self.canvas.zoom_out()
        self.zoom_out_requested.emit()

    def _reset_map_ui(self, data: dict) -> None:
        self._active_tool = TOOL_SELECT
        self._description_editor.close_editor()
        self._export_dialog.hide()
        self._select_panel.clear_selection()
        self.canvas.clear_selection()
        self.canvas.set_path_mode(False)
        self.canvas.set_path_submode(self._path_panel.selected_submode())
        self.canvas.set_pick_any_hex(False)
        self.canvas.set_brush_mode(False)
        self.canvas.set_pan_mode(False)
        self.canvas.set_erase_mode(False)
        self._tool_strip.set_active_tool(TOOL_SELECT)
        self._palette.apply_tool(TOOL_SELECT)
        self._toolbar.set_map_name(data.get("name", ""))
        self._members_bar.set_total(data.get("member_count", 0))
        self._body.sync_panels(TOOL_SELECT)
        self._body.reposition_panels()

    def selected_terrain(self) -> str | None:
        return self._palette.selected_terrain()

    def update_member_count(self, count: int) -> None:
        self._members_bar.set_total(count)

    def set_online_users(self, users: list[dict]) -> None:
        self._members_bar.set_users(users)
        self._body.reposition_panels()

    def apply_path_segment(self, path_id: str, waypoints: list, color: str) -> None:
        self._state.apply_path(path_id, waypoints, color)
        self.canvas.notify_state_changed()

    def remove_path(self, path_id: str) -> None:
        self._state.remove_path_by_id(path_id)
        self.canvas.notify_state_changed()

    def apply_edge_tiles(self, tiles: list[dict]) -> None:
        for tile in tiles:
            self._state.apply_edge_tile(tile)
        self.canvas.notify_state_changed()

    def apply_full_map_state(
        self,
        *,
        tiles: dict,
        paths: list[dict],
        edges: list[dict],
        online_users: list[dict],
        meta: dict,
    ) -> None:
        self._reset_map_ui(meta)
        self._state.set_tiles(tiles)
        self._state.set_paths(paths)
        self._state.set_edges(edges)
        self.canvas.notify_map_replaced()
        self.set_online_users(online_users)
        self.update_member_count(meta.get("member_count", 0))

    def refresh_inspector(self, q: int, r: int) -> None:
        self._select_panel.set_inspection(
            tile=self._state.tile_at(q, r),
            path_segments=self._state.path_segments_at(q, r),
            edge=self._state.edge_tile(q, r),
        )

    def set_inspector_details_loading(self) -> None:
        self._select_panel.set_details_loading()

    def set_inspector_server_details(
        self,
        details: dict | None,
        *,
        error: str = "",
    ) -> None:
        self._select_panel.set_server_details(details, error=error)

    def apply_server_tile(self, q: int, r: int, payload: dict) -> None:
        from models.map.tile_format import tile_from_server

        tile = tile_from_server(payload)
        if tile is None:
            self._state.remove_tile(q, r)
            self.canvas.notify_tile_removed(q, r)
        else:
            self._state.apply_tile(q, r, tile)
            self.canvas.notify_state_changed()

    def prompt_description(self, q: int, r: int) -> None:
        current = self._state.description_text(q, r)
        self._description_editor.open_for(q, r, current)

    def terrain_type_at(self, q: int, r: int) -> str | None:
        return self._state.terrain_type_at(q, r)

    def edge_snapshot(self, q: int, r: int) -> dict | None:
        return self._state.edge_snapshot(q, r)

    def hovered_erase_component(self) -> str | None:
        return self.canvas.hovered_erase_component()

    def hovered_path_id(self) -> str | None:
        return self.canvas.hovered_path_id()

    def hovered_edge(self):
        return self.canvas.hovered_edge()

    def path_by_id(self, path_id: str) -> dict | None:
        return self._state.path_by_id(path_id)

    def path_ids(self) -> set[str]:
        return self._state.path_ids()

    def open_export_dialog(self, default_path: str) -> None:
        self._export_dialog.open_for(default_path)

    def set_export_busy(self, busy: bool) -> None:
        self._export_dialog.set_busy(busy)

    def show_export_success(self, path: str) -> None:
        self._export_dialog.show_success(path)

    def show_export_error(self, message: str) -> None:
        self._export_dialog.show_error(message)

    def active_tool(self) -> str:
        return self._palette.active_tool()

    def set_undo_enabled(self, enabled: bool) -> None:
        self._tool_strip.set_undo_enabled(enabled)

    def set_redo_enabled(self, enabled: bool) -> None:
        self._tool_strip.set_redo_enabled(enabled)

    def export_full_map_image(self) -> QImage:
        return self.canvas.export_full_map_image()

    def show_error(self, message: str, *, duration_ms: int = 4000) -> None:
        self._error_banner.setWordWrap(True)
        self._error_banner.setText(message)
        self._error_banner.show()
        self._error_timer.start(duration_ms)
