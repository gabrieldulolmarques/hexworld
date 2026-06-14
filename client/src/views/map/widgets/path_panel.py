from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from views.map.widgets.constants import SIDE_PANEL_W
from views.map.widgets.hex_wheel import HexWheel
from views.map.widgets.map_panel import MapPanel, styled
from models.path_constants import DEFAULT_PATH_COLOR
from views.shared.widgets import horizontal_divider

_SAVED_COLS = 7
_MAX_SAVED_COLORS = _SAVED_COLS * 2
_SAVED_SWATCH = 42
_SAVED_GAP = 6

class PathColorPanel(MapPanel):
    path_color_selected = pyqtSignal(str)
    path_submode_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__("mapPathPanel")
        self.setFixedWidth(SIDE_PANEL_W)
        self._saved: list[str] = []

        heading = QLabel("PATH COLOR")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        submode_label = QLabel("PATH MODE")
        submode_label.setObjectName("fieldLabel")
        submode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._path_radio = QRadioButton("Path")
        self._edge_radio = QRadioButton("Edge")
        self._path_radio.setChecked(True)
        self._submode_group = QButtonGroup(self)
        self._submode_group.setExclusive(True)
        self._submode_group.addButton(self._path_radio)
        self._submode_group.addButton(self._edge_radio)
        self._path_radio.toggled.connect(self._on_submode_toggled)
        self._edge_radio.toggled.connect(self._on_submode_toggled)

        submode_row = QHBoxLayout()
        submode_row.setContentsMargins(0, 0, 0, 0)
        submode_row.setSpacing(32)
        submode_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        submode_row.addWidget(self._path_radio)
        submode_row.addWidget(self._edge_radio)

        self._wheel = HexWheel()
        self._wheel.color_picked.connect(self._on_wheel_pick)

        self._preview = QLabel()
        self._preview.setFixedSize(52, 52)
        self._preview.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._hex_input = QLineEdit()
        self._hex_input.setMaxLength(7)
        self._hex_input.setPlaceholderText("#rrggbb")
        self._hex_input.textChanged.connect(self._on_hex_changed)
        self._hex_input.editingFinished.connect(self._on_hex_edited)

        current_row = QHBoxLayout()
        current_row.setSpacing(12)
        current_row.addWidget(self._preview)
        current_row.addWidget(self._hex_input, 1)

        self._saved_label = QLabel("RECENTLY USED")
        self._saved_label.setObjectName("fieldLabel")
        self._saved_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._saved_label.hide()

        self._saved_rows_layout = QVBoxLayout()
        self._saved_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._saved_rows_layout.setSpacing(_SAVED_GAP)

        self._saved_wrap = QWidget()
        styled(self._saved_wrap)
        self._saved_wrap.setObjectName("pathSavedRow")
        self._saved_wrap.setFixedWidth(
            _SAVED_COLS * _SAVED_SWATCH + (_SAVED_COLS - 1) * _SAVED_GAP,
        )
        self._saved_wrap.setLayout(self._saved_rows_layout)
        self._saved_wrap.hide()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(heading)
        layout.addWidget(submode_label)
        layout.addLayout(submode_row)
        layout.addWidget(horizontal_divider())
        layout.addWidget(self._wheel, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(horizontal_divider())
        layout.addLayout(current_row)
        layout.addWidget(self._saved_label)
        layout.addWidget(self._saved_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("pathPanelScroll")
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setViewportMargins(0, 0, 2, 0)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._apply_color(DEFAULT_PATH_COLOR, emit=False)

    def apply_height_budget(self, max_h: int) -> int:
        self.setFixedHeight(max_h)
        return max_h

    def _on_submode_toggled(self, checked: bool) -> None:
        if not checked:
            return
        self.path_submode_changed.emit(self.selected_submode())

    def _on_wheel_pick(self, hex_str: str) -> None:
        self._apply_color(hex_str)
        self._add_saved(hex_str)

    def _on_hex_changed(self, text: str) -> None:
        normalized = text.strip()
        if not normalized.startswith("#"):
            normalized = "#" + normalized
        valid = QColor(normalized).isValid() and len(normalized) == 7
        self._hex_input.setStyleSheet("" if valid else "border: 1px solid #ef4444;")

    def _on_hex_edited(self) -> None:
        text = self._hex_input.text().strip()
        if not text.startswith("#"):
            text = "#" + text
        if QColor(text).isValid():
            self._apply_color(text)
            self._wheel.select_color(text)
            self._add_saved(text)

    def _apply_color(self, hex_str: str, *, emit: bool = True) -> None:
        self._preview.setStyleSheet(
            f"background-color: {hex_str}; border-radius: 8px;"
            " border: 1px solid rgba(255,255,255,0.15);"
        )
        if self._hex_input.text() != hex_str:
            self._hex_input.setText(hex_str)
        if emit:
            self.path_color_selected.emit(hex_str)

    def _add_saved(self, hex_str: str) -> None:
        if hex_str in self._saved:
            return
        self._saved.append(hex_str)
        if len(self._saved) > _MAX_SAVED_COLORS:
            self._saved.pop(0)
        self._saved_label.show()
        self._saved_wrap.show()
        self._rebuild_saved()

    def _rebuild_saved(self) -> None:
        while self._saved_rows_layout.count():
            item = self._saved_rows_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        for start in range(0, len(self._saved), _SAVED_COLS):
            chunk = self._saved[start : start + _SAVED_COLS]
            row_widget = QWidget()
            styled(row_widget)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(_SAVED_GAP)
            for color in chunk:
                swatch = QLabel()
                swatch.setFixedSize(_SAVED_SWATCH, _SAVED_SWATCH)
                swatch.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                swatch.setStyleSheet(
                    f"background-color: {color}; border-radius: 8px;"
                    " border: 1px solid rgba(255,255,255,0.12);"
                )
                swatch.setToolTip(color)
                swatch.setCursor(Qt.CursorShape.PointingHandCursor)
                swatch.mousePressEvent = lambda e, c=color: self._on_saved_click(c)
                row_layout.addWidget(swatch)
            self._saved_rows_layout.addWidget(
                row_widget,
                alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            )

    def _on_saved_click(self, hex_str: str) -> None:
        self._apply_color(hex_str)
        self._wheel.select_color(hex_str)

    def selected_color(self) -> str:
        return self._hex_input.text() or DEFAULT_PATH_COLOR

    def selected_submode(self) -> str:
        return "edge" if self._edge_radio.isChecked() else "path"
