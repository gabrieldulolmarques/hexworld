"""Vertical strip of mode (checkable) + action (one-shot) tool buttons."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QButtonGroup, QToolButton, QVBoxLayout

from styles.colors import GREEN_PRIMARY, GREEN_TINT, RED_PRIMARY, RED_TEXT

from views.map.constants import (
    TOOL_DESCRIPTION,
    TOOL_ERASE,
    TOOL_PAN,
    TOOL_ROAD,
    TOOL_SELECT,
    TOOL_STRUCTURE,
)
from views.map.icons import tinted_pixmap
from views.map.panel import MapPanel
from views.widgets import horizontal_divider

_TOOL_BTN_SIZE = 44

# Mode tools — checkable, exclusive (id, icon file, tooltip).
_TOOLS: tuple[tuple[str, str, str], ...] = (
    (TOOL_SELECT,      "tool-select.svg",      "Select"),
    (TOOL_PAN,         "tool-pan.svg",         "Pan"),
    (TOOL_STRUCTURE,   "tool-structure.svg",   "Structure"),
    (TOOL_ROAD,        "tool-road.svg",        "Road"),
    (TOOL_DESCRIPTION, "tool-description.svg", "Description"),
    (TOOL_ERASE,       "tool-erase.svg",       "Erase"),
)

# Action buttons — one-shot, not checkable.
_ACTIONS: tuple[tuple[str, str, str], ...] = (
    ("zoom_in",  "tool-zoom-in.svg",  "Zoom in"),
    ("zoom_out", "tool-zoom-out.svg", "Zoom out"),
    ("undo",     "tool-undo.svg",     "Undo"),
    ("redo",     "tool-redo.svg",     "Redo"),
    ("export",   "tool-export.svg",   "Export"),
)


class ToolStrip(MapPanel):
    tool_changed     = pyqtSignal(str)
    zoom_in_clicked  = pyqtSignal()
    zoom_out_clicked = pyqtSignal()
    undo_clicked     = pyqtSignal()
    redo_clicked     = pyqtSignal()
    export_clicked   = pyqtSignal()

    _ACTION_SIGNALS: dict[str, str] = {
        "zoom_in":  "zoom_in_clicked",
        "zoom_out": "zoom_out_clicked",
        "undo":     "undo_clicked",
        "redo":     "redo_clicked",
        "export":   "export_clicked",
    }

    def __init__(self) -> None:
        super().__init__("mapToolStrip")
        self._tool_ids: list[str] = []
        self._active_tool = TOOL_SELECT
        self._hovered_tool: str | None = None
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        col = QVBoxLayout(self)
        col.setContentsMargins(6, 8, 6, 8)
        col.setSpacing(6)

        for index, (tool_id, icon_file, tip) in enumerate(_TOOLS):
            btn = QToolButton()
            btn.setObjectName("mapToolBtn")
            btn.setFixedSize(_TOOL_BTN_SIZE, _TOOL_BTN_SIZE)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.setProperty("toolId", tool_id)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(QIcon(tinted_pixmap(icon_file, "#9f9fa9", 20)))
            btn.setIconSize(QSize(20, 20))
            btn.installEventFilter(self)
            self._btn_group.addButton(btn, index)
            self._tool_ids.append(tool_id)
            col.addWidget(btn)

        col.addWidget(horizontal_divider())
        col.addStretch(1)

        for action_id, icon_file, tip in _ACTIONS:
            btn = QToolButton()
            btn.setObjectName("mapToolBtn")
            btn.setFixedSize(_TOOL_BTN_SIZE, _TOOL_BTN_SIZE)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("toolId", action_id)
            btn.setIcon(QIcon(tinted_pixmap(icon_file, "#9f9fa9", 20)))
            btn.setIconSize(QSize(20, 20))
            btn.installEventFilter(self)
            signal_name = self._ACTION_SIGNALS[action_id]
            btn.clicked.connect(getattr(self, signal_name))
            col.addWidget(btn)

        self._btn_group.idClicked.connect(self._on_clicked)

        first = self._btn_group.button(0)
        if first:
            first.setChecked(True)
        self._sync_buttons(TOOL_SELECT)

    def eventFilter(self, obj, event) -> bool:
        if (
            isinstance(obj, QToolButton)
            and obj.objectName() == "mapToolBtn"
            and event.type() in (QEvent.Type.Enter, QEvent.Type.Leave)
        ):
            tool_id = obj.property("toolId")
            if event.type() == QEvent.Type.Enter:
                self._hovered_tool = tool_id
            elif self._hovered_tool == tool_id:
                self._hovered_tool = None
            self._update_button_icon(obj)
            return False
        return super().eventFilter(obj, event)

    def _icon_color(self, tool_id: str, *, active: bool) -> str:
        if active:
            return RED_PRIMARY if tool_id == TOOL_ERASE else GREEN_PRIMARY
        if self._hovered_tool == tool_id:
            return RED_TEXT if tool_id == TOOL_ERASE else GREEN_TINT
        return "#9f9fa9"

    def _update_button_icon(self, btn: QToolButton) -> None:
        tool_id = btn.property("toolId")
        if tool_id not in self._tool_ids:
            icon_file = next(
                (icon for aid, icon, _ in _ACTIONS if aid == tool_id),
                None,
            )
            if icon_file is None:
                return
            active = False
        else:
            icon_file = _TOOLS[self._tool_ids.index(tool_id)][1]
            active = tool_id == self._active_tool
        color = self._icon_color(tool_id, active=active)
        btn.setIcon(QIcon(tinted_pixmap(icon_file, color, 20)))

    def _on_clicked(self, index: int) -> None:
        if 0 <= index < len(self._tool_ids):
            tool_id = self._tool_ids[index]
            self._sync_buttons(tool_id)
            self.tool_changed.emit(tool_id)

    def set_active_tool(self, tool_id: str) -> None:
        idx = self._tool_ids.index(tool_id) if tool_id in self._tool_ids else -1
        if idx >= 0:
            btn = self._btn_group.button(idx)
            if btn:
                btn.setChecked(True)
        self._sync_buttons(tool_id)

    def _sync_buttons(self, active_id: str) -> None:
        self._active_tool = active_id
        for btn in self._btn_group.buttons():
            tid = btn.property("toolId")
            is_active = tid == active_id
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self._update_button_icon(btn)
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, QToolButton) and widget.objectName() == "mapToolBtn":
                self._update_button_icon(widget)
