"""Road panel — submode controls, curve actions, color picker and swatches."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from views.map.constants import SIDE_PANEL_W
from views.map.hex_wheel import HexWheel
from views.map.panel import MapPanel, styled
from views.widgets import horizontal_divider

_ROAD_COLOR_DEFAULT = "#5ea500"
_SAVED_COLS = 7
_MAX_SAVED_COLORS = _SAVED_COLS * 2   # 2 linhas × 7 colunas = 14
_SAVED_SWATCH = 42
_SAVED_GAP = 6


class RoadColorPanel(MapPanel):
    road_color_selected = pyqtSignal(str)
    road_submode_changed = pyqtSignal(str)  # "curve" | "inner_edge"

    def __init__(self) -> None:
        super().__init__("mapRoadPanel")
        self.setFixedWidth(SIDE_PANEL_W)
        self._saved: list[str] = []

        heading = QLabel("ROAD COLOR")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        submode_label = QLabel("ROAD MODE")
        submode_label.setObjectName("fieldLabel")
        submode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._curve_radio = QRadioButton("Curve road")
        self._inner_radio = QRadioButton("Inner edge")
        self._curve_radio.setChecked(True)
        self._submode_group = QButtonGroup(self)
        self._submode_group.setExclusive(True)
        self._submode_group.addButton(self._curve_radio)
        self._submode_group.addButton(self._inner_radio)
        self._curve_radio.toggled.connect(self._on_submode_toggled)
        self._inner_radio.toggled.connect(self._on_submode_toggled)

        submode_row = QHBoxLayout()
        submode_row.setContentsMargins(0, 0, 0, 0)
        submode_row.setSpacing(32)
        submode_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        submode_row.addWidget(self._curve_radio)
        submode_row.addWidget(self._inner_radio)

        self._wheel = HexWheel()
        self._wheel.color_picked.connect(self._on_wheel_pick)

        self._preview = QLabel()
        self._preview.setFixedSize(52, 52)
        self._preview.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._hex_input = QLineEdit()
        self._hex_input.setMaxLength(7)
        self._hex_input.setPlaceholderText("#rrggbb")
        self._hex_input.editingFinished.connect(self._on_hex_edited)

        current_row = QHBoxLayout()
        current_row.setSpacing(12)
        current_row.addWidget(self._preview)
        current_row.addWidget(self._hex_input, 1)

        saved_label = QLabel("RECENTLY USED")
        saved_label.setObjectName("fieldLabel")
        saved_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._saved_rows_layout = QVBoxLayout()
        self._saved_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._saved_rows_layout.setSpacing(_SAVED_GAP)

        self._saved_wrap = QWidget()
        styled(self._saved_wrap)
        self._saved_wrap.setObjectName("roadSavedRow")
        # tamanho fixo para 2 linhas × _SAVED_COLS colunas — nunca expande
        self._saved_wrap.setFixedSize(
            _SAVED_COLS * _SAVED_SWATCH + (_SAVED_COLS - 1) * _SAVED_GAP,
            2 * _SAVED_SWATCH + _SAVED_GAP,
        )
        self._saved_wrap.setLayout(self._saved_rows_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(submode_label)
        layout.addLayout(submode_row)
        layout.addWidget(horizontal_divider())
        layout.addWidget(self._wheel, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(horizontal_divider())
        layout.addLayout(current_row)
        layout.addWidget(saved_label)
        layout.addWidget(self._saved_wrap, 0, Qt.AlignmentFlag.AlignHCenter)

        self._apply_color(_ROAD_COLOR_DEFAULT, emit=False)

    def _on_submode_toggled(self, checked: bool) -> None:
        if not checked:
            return
        self.road_submode_changed.emit(self.selected_submode())

    def _on_wheel_pick(self, hex_str: str) -> None:
        self._apply_color(hex_str)
        self._add_saved(hex_str)

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
            self.road_color_selected.emit(hex_str)

    def _add_saved(self, hex_str: str) -> None:
        if hex_str in self._saved:
            return  # já salva, não duplicar nem mover
        self._saved.append(hex_str)          # nova cor vai para a direita
        if len(self._saved) > _MAX_SAVED_COLORS:
            self._saved.pop(0)               # remove a mais antiga (esquerda)
        self._rebuild_saved()

    def _rebuild_saved(self) -> None:
        while self._saved_rows_layout.count():
            item = self._saved_rows_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # type: ignore[arg-type]

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
                swatch.mousePressEvent = lambda e, c=color: self._on_saved_click(c)  # type: ignore[assignment]
                row_layout.addWidget(swatch)
            self._saved_rows_layout.addWidget(
                row_widget,
                alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            )

    def _on_saved_click(self, hex_str: str) -> None:
        self._apply_color(hex_str)
        self._wheel.select_color(hex_str)

    def selected_color(self) -> str:
        return self._hex_input.text() or _ROAD_COLOR_DEFAULT

    def selected_submode(self) -> str:
        return "inner_edge" if self._inner_radio.isChecked() else "curve"
