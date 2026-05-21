"""Right floating card — hex info once a hex is clicked."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout

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

        self._info = QTextBrowser()
        self._info.setObjectName("tileInfoBrowser")
        self._info.setOpenLinks(False)
        self._info.setReadOnly(True)
        self._info.document().setDefaultStyleSheet(
            "body { color: #d4d4d8; font-size: 14px; }"
            "h1, h2, h3 { color: #e4e4e7; margin: 4px 0; }"
            "code { color: #7ccf00; background: #27272a; padding: 1px 4px; border-radius: 3px; }"
            "hr { border: 0; border-top: 1px solid #3f3f46; margin: 8px 0; }"
            "strong { color: #e4e4e7; }"
            "p { margin: 4px 0; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(self._coord_label)
        layout.addWidget(self._info, 1)

    def has_selection(self) -> bool:
        return self._has_selection

    def clear_selection(self) -> None:
        self._has_selection = False
        self._coord_label.clear()
        self._info.clear()

    def set_coord(self, q: int, r: int) -> None:
        self._has_selection = True
        self._coord_label.setText(f"Hex ({q}, {r})")

    def set_tile_data(self, tile: dict | None) -> None:
        md = self._tile_markdown(tile)
        if md:
            self._info.setMarkdown(md)
        else:
            self._info.clear()

    @staticmethod
    def _tile_markdown(tile: dict | None) -> str:
        if not tile:
            return ""
        parts: list[str] = []
        if structure := tile.get("structure"):
            stype = structure.get("type", "unknown").capitalize()
            parts.append(f"**Structure:** {stype}")
        if road := tile.get("road"):
            color = road.get("color", "#5ea500")
            parts.append(f"**Road:** `{color}`")
        if desc := tile.get("description"):
            text = (desc.get("text") or "").strip()
            if text:
                if parts:
                    parts.append("---")
                parts.append(text)
        return "\n\n".join(parts)
