from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy

from views.map.panel import MapPanel

_HPAD = 40
_VPAD = 28

class MapToolbar(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapTopBar")
        self._raw_name = ""
        self._canvas_width = 0

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self._name_label = QLabel("")
        self._name_label.setObjectName("title")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setWordWrap(False)
        self._name_label.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )

        font = QFont(self._name_label.font())
        font.setPixelSize(21)
        font.setWeight(QFont.Weight.Bold)
        self._name_label.setFont(font)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        root.addWidget(self._name_label)

    def set_map_name(self, name: str) -> None:
        self._raw_name = name or ""
        self._apply_name_layout()

    def refresh_name_label(self, canvas_width: int = 0) -> None:
        if canvas_width > 0:
            self._canvas_width = canvas_width
        self._apply_name_layout()

    def _max_inner_width(self) -> int:
        if self._canvas_width > 160:
            return self._canvas_width - 80 - _HPAD
        parent = self.parent()
        if parent is not None and parent.width() > 160:
            return parent.width() - 80 - _HPAD
        return 800

    def _apply_name_layout(self) -> None:
        if not self._raw_name:
            self._name_label.setText("")
            self._name_label.setToolTip("")
            self.setFixedSize(_HPAD, 50)
            return

        metrics = QFontMetrics(self._name_label.font())
        text_w = metrics.horizontalAdvance(self._raw_name)
        text_h = metrics.height()
        inner_cap = self._max_inner_width()

        if text_w <= inner_cap:
            display = self._raw_name
            inner_w = text_w
            self._name_label.setToolTip("")
        else:
            inner_w = inner_cap
            display = metrics.elidedText(
                self._raw_name, Qt.TextElideMode.ElideRight, inner_w,
            )
            self._name_label.setToolTip(self._raw_name)

        self._name_label.setText(display)
        self._name_label.setFixedSize(max(inner_w, 1), text_h)
        self.setFixedSize(inner_w + _HPAD, text_h + _VPAD)
