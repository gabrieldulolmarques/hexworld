from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from views.hex_canvas import HexCanvas
from views.map.body import MapBody
from views.map.constants import TOOL_DESCRIPTION, TOOL_ERASE, TOOL_PAN, TOOL_ROAD, TOOL_SELECT, TOOL_STRUCTURE
from views.map.description_editor import DescriptionEditor
from views.map.export_dialog import ExportDialog
from views.map.members_bar import MembersBar
from views.map.minimap import MinimapWidget
from views.map.palette_panel import PalettePanel
from views.map.panel import styled
from views.map.road_panel import RoadColorPanel
from views.map.select_panel import SelectPanel
from views.map.tool_strip import ToolStrip
from views.map.toolbar import MapToolbar

__all__ = [
    "MapView",
    "TOOL_SELECT",
    "TOOL_STRUCTURE",
    "TOOL_ROAD",
    "TOOL_DESCRIPTION",
    "TOOL_ERASE",
    "TOOL_PAN",
]

class MapView(QWidget):
    request_back        = pyqtSignal()
    hex_selected        = pyqtSignal(int, int)
    hex_paint_clicked   = pyqtSignal(int, int)
    structure_selected   = pyqtSignal(str)
    road_color_selected  = pyqtSignal(str)
    path_drawn           = pyqtSignal(list, str)
    road_drawn           = path_drawn
    inner_edge_painted   = pyqtSignal(int, int, int, str)
    tool_changed         = pyqtSignal(str)
    description_submitted = pyqtSignal(int, int, str)
    zoom_in_requested    = pyqtSignal()
    zoom_out_requested   = pyqtSignal()
    undo_requested       = pyqtSignal()
    redo_requested       = pyqtSignal()
    export_requested     = pyqtSignal()
    export_submitted     = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mapScreen")
        styled(self)
        self._active_tool = TOOL_SELECT
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.canvas = HexCanvas()
        self.canvas.setObjectName("hexCanvas")
        self.canvas.hex_clicked.connect(self._on_hex_clicked)
        self.canvas.hex_deselected.connect(self._on_hex_deselected)

        self._toolbar             = MapToolbar()
        self._select_panel        = SelectPanel()
        self._members_bar         = MembersBar()
        self._tool_strip          = ToolStrip()
        self._palette             = PalettePanel()
        self._road_panel          = RoadColorPanel()
        self._description_editor  = DescriptionEditor()
        self._export_dialog       = ExportDialog()
        self._minimap             = MinimapWidget(self.canvas)

        self._members_bar.connect_back(self.request_back)
        self._palette.structure_selected.connect(self.structure_selected)
        self._road_panel.road_color_selected.connect(self.road_color_selected)
        self._road_panel.road_color_selected.connect(self.canvas.set_road_color)
        self._road_panel.road_submode_changed.connect(self._on_road_submode_changed)
        self.canvas.path_drawn.connect(self.path_drawn)
        self.canvas.inner_edge_painted.connect(self.inner_edge_painted)
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
            self._road_panel,
            self._description_editor,
            self._export_dialog,
            self._minimap,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._body, 1)
        self._body.sync_panels(TOOL_SELECT)

    def _on_hex_clicked(self, q: int, r: int) -> None:
        self._select_panel.set_coord(q, r)
        if self._active_tool == TOOL_SELECT:
            self.refresh_inspector(q, r)
            self.hex_selected.emit(q, r)
            self._body.sync_panels(TOOL_SELECT)
        elif self._active_tool in (TOOL_STRUCTURE, TOOL_DESCRIPTION, TOOL_ERASE):

            self.hex_paint_clicked.emit(q, r)

    def _on_hex_deselected(self) -> None:
        self._select_panel.clear_selection()
        if self._active_tool == TOOL_SELECT:
            self._body.sync_panels(TOOL_SELECT)

    def _on_tool_changed(self, tool_id: str) -> None:
        if tool_id != TOOL_SELECT:
            self._select_panel.clear_selection()
            self.canvas.clear_selection()
        self._active_tool = tool_id
        self._palette.apply_tool(tool_id)
        self._body.sync_panels(tool_id)
        self.canvas.set_pick_any_hex(
            tool_id in (TOOL_STRUCTURE, TOOL_DESCRIPTION, TOOL_ROAD),
        )
        self.canvas.set_erase_mode(tool_id == TOOL_ERASE)
        self.canvas.set_brush_mode(tool_id in (TOOL_STRUCTURE, TOOL_ERASE))
        self.canvas.set_pan_mode(tool_id == TOOL_PAN)
        self.canvas.set_road_mode(
            tool_id == TOOL_ROAD, self._road_panel.selected_color(),
        )
        if tool_id == TOOL_ROAD:
            self.canvas.set_road_submode(self._road_panel.selected_submode())
        self.tool_changed.emit(tool_id)

    def _on_road_submode_changed(self, submode: str) -> None:
        self.canvas.set_road_submode(submode)
        self._body.reposition_panels()

    def _on_zoom_in(self) -> None:
        self.canvas.zoom_in()
        self.zoom_in_requested.emit()

    def _on_zoom_out(self) -> None:
        self.canvas.zoom_out()
        self.zoom_out_requested.emit()

    def set_map(self, data: dict) -> None:
        self._active_tool = TOOL_SELECT
        self._description_editor.close_editor()
        self._export_dialog.hide()
        self._select_panel.clear_selection()
        self.canvas.clear_selection()
        self.canvas.set_roads([])
        self.canvas.set_inner_edges([])
        self.canvas.set_road_mode(False)
        self.canvas.set_road_submode(self._road_panel.selected_submode())
        self.canvas.set_pick_any_hex(False)
        self.canvas.set_brush_mode(False)
        self.canvas.set_pan_mode(False)
        self._tool_strip.set_active_tool(TOOL_SELECT)
        self._palette.apply_tool(TOOL_SELECT)
        self._toolbar.set_map_name(data.get("name", ""))
        self._members_bar.set_total(data.get("member_count", 0))
        self._body.sync_panels(TOOL_SELECT)
        self._body.reposition_panels()

    def selected_structure(self) -> str | None:
        return self._palette.selected_structure()

    def update_member_count(self, count: int) -> None:
        self._members_bar.set_total(count)

    def set_online_users(self, users: list[dict]) -> None:
        self._members_bar.set_users(users)
        self._body.reposition_panels()

    def set_tiles(self, tiles: dict) -> None:
        self.canvas.set_tiles(tiles)

    def apply_tile(self, q: int, r: int, data: dict) -> None:
        self.canvas.apply_tile(q, r, data)

    def refresh_inspector(self, q: int, r: int) -> None:
        self._select_panel.set_inspection(
            tile=self.canvas.tile_at(q, r),
            road_segments=self.canvas.road_segments_at(q, r),
            inner_edge=self.canvas.inner_edge_cell(q, r),
        )

    def set_inspector_details_loading(self) -> None:
        self._select_panel.set_details_loading()

    def set_inspector_server_details(
        self, details: dict | None, *, error: str = "",
    ) -> None:
        self._select_panel.set_server_details(details, error=error)

    def apply_server_tile(self, q: int, r: int, payload: dict) -> None:
        from models.tile_format import tile_from_server

        tile = tile_from_server(payload)
        if tile is None:
            self.canvas.remove_tile(q, r)
        else:
            self.canvas.apply_tile(q, r, tile)

    def prompt_description(self, q: int, r: int) -> None:
        current = self.canvas.description_text(q, r)
        self._description_editor.open_for(q, r, current)

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

    def set_active_tool(self, tool_id: str) -> None:
        self._tool_strip.set_active_tool(tool_id)
        self._palette.apply_tool(tool_id)
