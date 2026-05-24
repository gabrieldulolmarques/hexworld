from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from models.asset_registry import REGISTRY
from views.map.constants import SIDE_PANEL_W, TOOL_DESCRIPTION, TOOL_SELECT, TOOL_STRUCTURE
from views.map.panel import MapPanel, styled

_BIOMES_WITH_EMPTY = frozenset({
    "deadlands",
    "drylands",
    "greenlands",
    "icelands",
    "sandlands",
})

_EMPTY_CAT = "empty"

_BIOME_LABELS: dict[str, str] = {
    _EMPTY_CAT:   "Empty",
    "deadlands":  "Dead",
    "drylands":   "Dry",
    "forest":     "Forest",
    "greenlands": "Green",
    "icelands":   "Ice",
    "mountain":   "Mountain",
    "sandlands":  "Sand",
}

_THUMB_SIZE = 44
_TILE_BTN_H = 150

_PANEL_HEADINGS: dict[str, str] = {
    TOOL_STRUCTURE: "STRUCTURE",
    TOOL_DESCRIPTION: "DESCRIPTION",
}

class TileButton(QWidget):
    clicked_signal = pyqtSignal()

    def __init__(self, pixmap: QPixmap | None, label: str) -> None:
        super().__init__()
        self.setObjectName("tileBtn")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        _px = _THUMB_SIZE * 2

        icon_lbl = QLabel()
        icon_lbl.setObjectName("tileBtnIcon")
        icon_lbl.setFixedSize(_px, _px)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if pixmap and not pixmap.isNull():
            icon_lbl.setPixmap(pixmap)

        text_lbl = QLabel(label)
        text_lbl.setObjectName("tileBtnLabel")
        text_lbl.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        text_lbl.setWordWrap(True)
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)
        layout.addWidget(icon_lbl, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_lbl)

    def set_checked(self, checked: bool) -> None:
        self.setProperty("checked", "true" if checked else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def enterEvent(self, event) -> None:
        self.setProperty("hovered", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.setProperty("hovered", "false")
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit()
        super().mousePressEvent(event)

class PalettePanel(MapPanel):
    structure_selected = pyqtSignal(str)
    tool_changed = pyqtSignal(str)

    _PANEL_PAD    = 24
    _SCROLL_GUTTER = 16
    _COLS    = 2
    _GRID_GAP = 10
    _BTN_W = (
        SIDE_PANEL_W
        - 2 * _PANEL_PAD
        - _SCROLL_GUTTER
        - (_COLS - 1) * _GRID_GAP
    ) // _COLS

    _BIOME_COLS = 4
    _STRIP_PAD  = 6
    _TAB_HGAP   = 6
    _TAB_H      = 36
    _TAB_W      = (
        SIDE_PANEL_W - 2 * _PANEL_PAD - 2 * _STRIP_PAD - (_BIOME_COLS - 1) * _TAB_HGAP
    ) // _BIOME_COLS

    def __init__(self) -> None:
        super().__init__("mapPalette")
        self.setFixedWidth(SIDE_PANEL_W)
        self._active_tile: TileButton | None = None
        self._structure_stem: str | None = None
        self._active_tool = TOOL_SELECT
        self._biome_list = [_EMPTY_CAT] + REGISTRY.biomes()

        self._tab_strip = QWidget()
        self._tab_strip.setObjectName("biomeTabStrip")
        styled(self._tab_strip)
        strip_lay = QVBoxLayout(self._tab_strip)
        strip_lay.setContentsMargins(
            self._STRIP_PAD, self._STRIP_PAD, self._STRIP_PAD, self._STRIP_PAD,
        )
        strip_lay.setSpacing(self._TAB_HGAP)

        self._biome_group = QButtonGroup(self)
        self._biome_group.setExclusive(True)

        n = len(self._biome_list)
        rows = (n + self._BIOME_COLS - 1) // self._BIOME_COLS
        for r in range(rows):
            row_lay = QHBoxLayout()
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(self._TAB_HGAP)
            for c in range(self._BIOME_COLS):
                i = r * self._BIOME_COLS + c
                if i >= n:
                    row_lay.addStretch()
                    continue
                biome = self._biome_list[i]
                label = _BIOME_LABELS.get(biome, biome.capitalize())
                tab = QToolButton()
                tab.setObjectName("biomeTab")
                tab.setText(label)
                tab.setCheckable(True)
                tab.setFixedSize(self._TAB_W, self._TAB_H)
                self._biome_group.addButton(tab, i)
                row_lay.addWidget(tab)
            strip_lay.addLayout(row_lay)

        self._biome_group.idClicked.connect(self._on_biome_clicked)

        self._grid_widget = QWidget()
        self._grid_widget.setObjectName("paletteGrid")
        styled(self._grid_widget)
        self._grid_widget.setFixedWidth(
            self._COLS * self._BTN_W + (self._COLS - 1) * self._GRID_GAP
        )
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 2, 0, 2)
        self._grid_layout.setHorizontalSpacing(self._GRID_GAP)
        self._grid_layout.setVerticalSpacing(self._GRID_GAP)
        self._grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        for c in range(self._COLS):
            self._grid_layout.setColumnMinimumWidth(c, self._BTN_W)

        scroll = QScrollArea()
        scroll.setObjectName("paletteScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._grid_widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setViewportMargins(0, 0, 2, 0)
        scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        styled(scroll)
        scroll.viewport().setStyleSheet("background-color: #18181b;")
        self._scroll = scroll

        self._structure_area = QWidget()
        self._structure_area.setObjectName("mapStructureArea")
        self._structure_area.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        styled(self._structure_area)
        structure_lay = QVBoxLayout(self._structure_area)
        structure_lay.setContentsMargins(0, 0, 0, 0)
        structure_lay.setSpacing(8)
        structure_lay.addWidget(self._tab_strip)
        structure_lay.addWidget(self._scroll, 1)

        self._heading = QLabel("STRUCTURE")
        self._heading.setObjectName("panelTitle")
        self._heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._heading)
        layout.addWidget(self._structure_area, 1)

        self._apply_tool(TOOL_SELECT, emit=False)

        first = self._biome_group.button(0)
        if first:
            first.setChecked(True)
        self._on_biome_clicked(0)

    def _on_biome_clicked(self, index: int) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._active_tile = None

        if index >= len(self._biome_list):
            return

        biome = self._biome_list[index]
        if biome == _EMPTY_CAT:
            entries = [
                (info, _BIOME_LABELS.get(info.biome, info.biome.capitalize()))
                for b in _BIOMES_WITH_EMPTY
                for info in REGISTRY.tiles(b)
                if info.key == "empty"
            ]
        else:
            entries = [
                (info, info.label)
                for info in REGISTRY.tiles(biome)
                if info.key != "empty"
            ]

        for i, (info, label) in enumerate(entries):
            pixmap = REGISTRY.pixmap(info.stem, _THUMB_SIZE)
            btn = TileButton(pixmap, label)
            btn.setFixedSize(self._BTN_W, _TILE_BTN_H)
            btn.clicked_signal.connect(
                lambda stem=info.stem, b=btn: self._on_tile_clicked(b, stem),
            )
            self._grid_layout.addWidget(btn, i // self._COLS, i % self._COLS)

        self._sync_scroll_to_grid()
        self._notify_layout_changed()

    def _grid_content_height(self, tile_count: int) -> int:
        if tile_count <= 0:
            return 0
        rows = (tile_count + self._COLS - 1) // self._COLS
        return (
            rows * _TILE_BTN_H
            + max(0, rows - 1) * self._GRID_GAP
            + self._grid_layout.contentsMargins().top()
            + self._grid_layout.contentsMargins().bottom()
        )

    def _sync_scroll_to_grid(self) -> None:
        count = self._grid_layout.count()
        self._grid_widget.setMinimumHeight(self._grid_content_height(count))

    def apply_height_budget(self, max_h: int) -> int:
        self.setFixedHeight(max_h)
        return max_h

    def _notify_layout_changed(self) -> None:
        self.adjustSize()
        parent = self.parent()
        if parent is not None and hasattr(parent, "reposition_panels"):
            parent.reposition_panels()

    def apply_tool(self, tool_id: str) -> None:
        self._apply_tool(tool_id)

    def _apply_tool(self, tool_id: str, *, emit: bool = True) -> None:
        changed = tool_id != self._active_tool
        self._active_tool = tool_id

        heading = _PANEL_HEADINGS.get(tool_id, "")
        self._heading.setText(heading)
        self._heading.setVisible(bool(heading))
        self._structure_area.setVisible(tool_id == TOOL_STRUCTURE)

        if emit and changed:
            self.tool_changed.emit(tool_id)
        self._notify_layout_changed()

    def active_tool(self) -> str:
        return self._active_tool

    def selected_structure(self) -> str | None:
        return self._structure_stem

    def _on_tile_clicked(self, btn: TileButton, stem: str) -> None:
        if self._active_tool != TOOL_STRUCTURE:
            return
        if self._active_tile and self._active_tile is not btn:
            self._active_tile.set_checked(False)
        self._active_tile = btn
        self._structure_stem = stem
        btn.set_checked(True)
        self.structure_selected.emit(stem)
