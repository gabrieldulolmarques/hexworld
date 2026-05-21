"""Top-center toolbar — shows the active map name."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel

from views.map.panel import MapPanel


class MapToolbar(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapTopBar")

        self._name_label = QLabel("")
        self._name_label.setObjectName("title")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.addWidget(self._name_label)

    def set_map_name(self, name: str) -> None:
        self._name_label.setText(name)
        self.adjustSize()
