"""Top-center toolbar — shows the active map name."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QLabel

from views.map.panel import MapPanel


class MapToolbar(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapTopBar")
        self._raw_name = ""

        self._name_label = QLabel("")
        self._name_label.setObjectName("title")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.addWidget(self._name_label)

    def set_map_name(self, name: str) -> None:
        self._raw_name = name
        self._apply_elide()
        self.adjustSize()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        avail = max(40, self.width() - 40)
        metrics = QFontMetrics(self._name_label.font())
        elided = metrics.elidedText(self._raw_name, Qt.TextElideMode.ElideRight, avail)
        self._name_label.setText(elided)
        self._name_label.setToolTip(self._raw_name if elided != self._raw_name else "")
