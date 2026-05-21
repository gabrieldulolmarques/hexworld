"""Right floating card — hex info once a hex is clicked."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout

from views.map.constants import SIDE_PANEL_W
from views.map.panel import MapPanel


class SelectPanel(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapSelectPanel")
        self.setFixedWidth(SIDE_PANEL_W)
        self._has_selection = False

        heading = QLabel("INSPECTOR")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._coord_label = QLabel()
        self._coord_label.setObjectName("title")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(self._coord_label)
        layout.addStretch(1)

    def has_selection(self) -> bool:
        return self._has_selection

    def clear_selection(self) -> None:
        self._has_selection = False
        self._coord_label.clear()

    def set_coord(self, q: int, r: int) -> None:
        self._has_selection = True
        self._coord_label.setText(f"Hex ({q}, {r})")
