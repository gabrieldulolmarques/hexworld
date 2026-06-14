from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from views.map.canvas.map_canvas import MapCanvas
from models.map.tool_ids import TOOL_PATH, TOOL_SELECT, TOOL_TERRAIN
from views.map.widgets.constants import PANEL_MARGIN, PANEL_MIN_H, RIGHT_COLUMN_GAP
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

class MapBody(QWidget):
    def __init__(
        self,
        canvas: MapCanvas,
        toolbar: MapToolbar,
        select_panel: SelectPanel,
        members_bar: MembersBar,
        tool_strip: ToolStrip,
        palette: PalettePanel,
        path_panel: PathColorPanel,
        description_editor: DescriptionEditor,
        export_dialog: ExportDialog,
        minimap: MinimapWidget,
    ) -> None:
        super().__init__()
        self.setObjectName("mapCanvasArea")
        styled(self)
        self._toolbar = toolbar
        self._select_panel = select_panel
        self._members_bar = members_bar
        self._tool_strip = tool_strip
        self._palette = palette
        self._path_panel = path_panel
        self._description_editor = description_editor
        self._export_dialog = export_dialog
        self._minimap = minimap

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

        for panel in (
            select_panel,
            members_bar,
            tool_strip,
            path_panel,
            palette,
            toolbar,
            minimap,
        ):
            panel.setParent(self)
            panel.raise_()

        description_editor.setParent(self)
        description_editor.hide()
        export_dialog.setParent(self)
        export_dialog.hide()

        select_panel.hide()
        path_panel.hide()
        palette.hide()

        members_bar.toggled.connect(self._place_members_bar)
        members_bar.geometry_changed.connect(self._place_members_bar)
        self._reposition_timer = QTimer(self)
        self._reposition_timer.setSingleShot(True)
        self._reposition_timer.setInterval(0)
        self._reposition_timer.timeout.connect(self._reposition_panels_impl)
        self.sync_panels(TOOL_SELECT)

    def sync_panels(self, tool_id: str) -> None:
        show_select = tool_id == TOOL_SELECT and self._select_panel.has_selection()
        self._select_panel.setVisible(show_select)
        self._palette.setVisible(tool_id == TOOL_TERRAIN)
        self._path_panel.setVisible(tool_id == TOOL_PATH)
        self._reposition_panels()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_panels()

    def reposition_panels(self) -> None:
        self._reposition_panels()

    def _reposition_panels(self) -> None:
        if not self._reposition_timer.isActive():
            self._reposition_timer.start()

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

        mm = self._minimap
        mm.move(w - mm.width() - m, h - mm.height() - m)
        right_budget = max(PANEL_MIN_H, mm.y() - m - RIGHT_COLUMN_GAP)

        sp = self._select_panel
        sp.apply_height_budget(right_budget)
        sp.move(w - sp.width() - m, m)

        self._place_members_bar()

        pal = self._palette
        pal.apply_height_budget(right_budget)
        pal.move(w - pal.width() - m, m)

        rp = self._path_panel
        rp.apply_height_budget(right_budget)
        rp.move(w - rp.width() - m, m)

        self._description_editor.setGeometry(self.rect())
        self._export_dialog.setGeometry(self.rect())

    def _place_members_bar(self) -> None:
        m = PANEL_MARGIN
        h = self.height()
        mb = self._members_bar
        budget = max(0, h - 2 * m)
        bar_h = mb.apply_height_budget(budget)
        mb.resize(mb.width(), bar_h)
        mb.move(m, max(m, h - bar_h - m))
