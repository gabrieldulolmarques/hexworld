"""MapBody — hosts the canvas and positions all overlay panels."""

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from views.hex_canvas import HexCanvas
from views.map.constants import (
    PANEL_MARGIN,
    TOOL_ROAD,
    TOOL_SELECT,
    TOOL_STRUCTURE,
)
from views.map.description_editor import DescriptionEditor
from views.map.export_dialog import ExportDialog
from views.map.members_bar import MembersBar
from views.map.palette_panel import PalettePanel
from views.map.panel import styled
from views.map.road_panel import RoadColorPanel
from views.map.select_panel import SelectPanel
from views.map.tool_strip import ToolStrip
from views.map.toolbar import MapToolbar


class MapBody(QWidget):
    """Canvas with all floating panels as overlays."""

    def __init__(
        self,
        canvas: HexCanvas,
        toolbar: MapToolbar,
        select_panel: SelectPanel,
        members_bar: MembersBar,
        tool_strip: ToolStrip,
        palette: PalettePanel,
        road_panel: RoadColorPanel,
        description_editor: DescriptionEditor,
        export_dialog: ExportDialog,
    ) -> None:
        super().__init__()
        self.setObjectName("mapCanvasArea")
        styled(self)
        self._toolbar = toolbar
        self._select_panel = select_panel
        self._members_bar = members_bar
        self._tool_strip = tool_strip
        self._palette = palette
        self._road_panel = road_panel
        self._description_editor = description_editor
        self._export_dialog = export_dialog

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

        for panel in (select_panel, members_bar, tool_strip, road_panel, palette, toolbar):
            panel.setParent(self)
            panel.raise_()

        description_editor.setParent(self)
        description_editor.hide()
        export_dialog.setParent(self)
        export_dialog.hide()

        select_panel.hide()
        road_panel.hide()
        palette.hide()

        members_bar.toggled.connect(self._place_members_bar)
        members_bar.geometry_changed.connect(self._place_members_bar)
        self._repositioning = False
        self.sync_panels(TOOL_SELECT)

    def sync_panels(self, tool_id: str) -> None:
        show_select = tool_id == TOOL_SELECT and self._select_panel.has_selection()
        self._select_panel.setVisible(show_select)
        self._palette.setVisible(tool_id == TOOL_STRUCTURE)
        self._road_panel.setVisible(tool_id == TOOL_ROAD)
        self._reposition_panels()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_panels()

    def reposition_panels(self) -> None:
        """Public alias for code outside the package."""
        self._reposition_panels()

    def _reposition_panels(self) -> None:
        if self._repositioning:
            return
        self._repositioning = True
        try:
            self._reposition_panels_impl()
        finally:
            self._repositioning = False

    def _reposition_panels_impl(self) -> None:
        m = PANEL_MARGIN
        w = self.width()
        h = self.height()

        bar = self._toolbar
        bar.refresh_name_label(w)
        bar.move(max(m, (w - bar.width()) // 2), m)

        ts = self._tool_strip
        ts.adjustSize()
        ts.move(m, m)

        sp = self._select_panel
        sp.setFixedHeight(max(200, h - 2 * m))
        sp.move(w - sp.width() - m, m)

        self._place_members_bar()

        pal = self._palette
        pal.setFixedHeight(max(200, h - 2 * m))
        pal.move(w - pal.width() - m, m)

        rp = self._road_panel
        rp.adjustSize()
        rp.move(w - rp.width() - m, m)

        self._description_editor.setGeometry(self.rect())
        self._export_dialog.setGeometry(self.rect())

    def _place_members_bar(self) -> None:
        """Anchor members bar to the bottom-left without shifting other panels."""
        m = PANEL_MARGIN
        h = self.height()
        mb = self._members_bar
        budget = max(0, h - 2 * m)
        bar_h = mb.apply_height_budget(budget)
        mb.resize(mb.width(), bar_h)
        mb.move(m, max(m, h - bar_h - m))
