"""Map editor top-level view.

This module is a thin facade that composes the floating panels defined
under :mod:`views.map` into the user-facing ``MapView`` widget. All Qt
signals exposed here are wired to the underlying sub-widgets.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from views.hex_canvas import HexCanvas
from views.map.body import MapBody
from views.map.constants import (
    TOOL_DESCRIPTION,
    TOOL_ERASE,
    TOOL_PAN,
    TOOL_ROAD,
    TOOL_SELECT,
    TOOL_STRUCTURE,
)
from views.map.description_editor import DescriptionEditor
from views.map.members_bar import MembersBar
from views.map.palette_panel import PalettePanel
from views.map.panel import styled
from views.map.road_panel import RoadColorPanel
from views.map.select_panel import SelectPanel
from views.map.tool_strip import ToolStrip
from views.map.toolbar import MapToolbar

# Re-exported tool IDs (kept for backwards compatibility with callers
# that previously imported them from ``views.map_view``).
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
    tool_changed         = pyqtSignal(str)
    description_submitted = pyqtSignal(int, int, str)  # q, r, text
    zoom_in_requested    = pyqtSignal()
    zoom_out_requested   = pyqtSignal()
    undo_requested       = pyqtSignal()
    redo_requested       = pyqtSignal()
    export_requested     = pyqtSignal()

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
        self.canvas.hex_clicked.connect(self.hex_selected)

        self._toolbar             = MapToolbar()
        self._select_panel        = SelectPanel()
        self._members_bar         = MembersBar()
        self._tool_strip          = ToolStrip()
        self._palette             = PalettePanel()
        self._road_panel          = RoadColorPanel()
        self._description_editor  = DescriptionEditor()

        self._members_bar.connect_back(self.request_back)
        self._palette.structure_selected.connect(self.structure_selected)
        self._road_panel.road_color_selected.connect(self.road_color_selected)
        self._tool_strip.tool_changed.connect(self._on_tool_changed)
        self._tool_strip.zoom_in_clicked.connect(self._on_zoom_in)
        self._tool_strip.zoom_out_clicked.connect(self._on_zoom_out)
        self._tool_strip.undo_clicked.connect(self.undo_requested)
        self._tool_strip.redo_clicked.connect(self.redo_requested)
        self._tool_strip.export_clicked.connect(self.export_requested)
        self._description_editor.submitted.connect(self.description_submitted)

        self._body = MapBody(
            self.canvas,
            self._toolbar,
            self._select_panel,
            self._members_bar,
            self._tool_strip,
            self._palette,
            self._road_panel,
            self._description_editor,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._body, 1)
        self._body.sync_panels(TOOL_SELECT)

    # ------------------------------------------------------------------
    # Internal signal handlers
    # ------------------------------------------------------------------

    def _on_hex_clicked(self, q: int, r: int) -> None:
        self._select_panel.set_coord(q, r)
        if self._active_tool == TOOL_SELECT:
            self._select_panel.set_tile_data(self.canvas.tile_at(q, r))
            self._body.sync_panels(TOOL_SELECT)
        elif self._active_tool in (TOOL_STRUCTURE, TOOL_ROAD, TOOL_DESCRIPTION, TOOL_ERASE):
            self.hex_paint_clicked.emit(q, r)

    def _on_hex_deselected(self) -> None:
        self._select_panel.clear_selection()
        if self._active_tool == TOOL_SELECT:
            self._body.sync_panels(TOOL_SELECT)

    def _on_tool_changed(self, tool_id: str) -> None:
        self._active_tool = tool_id
        self._palette.apply_tool(tool_id)
        self._body.sync_panels(tool_id)
        self.canvas.set_pick_any_hex(
            tool_id in (TOOL_STRUCTURE, TOOL_ROAD, TOOL_DESCRIPTION),
        )
        self.canvas.set_erase_mode(tool_id == TOOL_ERASE)
        self.tool_changed.emit(tool_id)

    def _on_zoom_in(self) -> None:
        self.canvas.zoom_in()
        self.zoom_in_requested.emit()

    def _on_zoom_out(self) -> None:
        self.canvas.zoom_out()
        self.zoom_out_requested.emit()

    # ------------------------------------------------------------------
    # Public API (controller)
    # ------------------------------------------------------------------

    def selected_road_color(self) -> str:
        return self._road_panel.selected_color()

    def set_map(self, data: dict) -> None:
        self._active_tool = TOOL_SELECT
        self._description_editor.close_editor()
        self._select_panel.clear_selection()
        self.canvas.clear_selection()
        self.canvas.set_pick_any_hex(False)
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

    def apply_server_tile(self, q: int, r: int, payload: dict) -> None:
        """RF17: apply full server tile snapshot (or clear hex if empty)."""
        from models.tile_format import tile_from_server

        tile = tile_from_server(payload)
        if tile is None:
            self.canvas.remove_tile(q, r)
        else:
            self.canvas.apply_tile(q, r, tile)

    def prompt_description(self, q: int, r: int) -> None:
        current = self.canvas.description_text(q, r)
        self._description_editor.open_for(q, r, current)

    def close_description_editor(self) -> None:
        self._description_editor.close_editor()

    def active_tool(self) -> str:
        return self._palette.active_tool()

    def set_active_tool(self, tool_id: str) -> None:
        self._tool_strip.set_active_tool(tool_id)
        self._palette.apply_tool(tool_id)
