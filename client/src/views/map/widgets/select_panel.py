from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.map.widgets.constants import SIDE_PANEL_W
from views.map.widgets.inspector.connections_section import (
    build_connections_section,
    connection_row_count,
    connections_scroll_height,
)
from views.map.widgets.inspector.description_section import build_description_card
from views.map.widgets.inspector.footer_section import build_footer_card
from views.map.widgets.inspector.terrain_section import build_terrain_header
from views.map.widgets.map_panel import MapPanel

class SelectPanel(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapSelectPanel")
        self.setFixedWidth(SIDE_PANEL_W)
        self._has_selection = False
        self._loading = False
        self._server_error = ""
        self._server_details: dict | None = None
        self._local_tile: dict | None = None
        self._local_paths: list[dict] = []
        self._local_edge: dict | None = None

        heading = QLabel("INSPECTOR")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._coord_label = QLabel()
        self._coord_label.setObjectName("title")
        self._coord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._terrain_host = QWidget()
        self._terrain_host.setObjectName("inspectorTerrainHost")
        self._terrain_layout = QVBoxLayout(self._terrain_host)
        self._terrain_layout.setContentsMargins(0, 0, 0, 0)
        self._terrain_host.hide()

        self._desc_host = QWidget()
        self._desc_host.setObjectName("inspectorDescHost")
        self._desc_layout = QVBoxLayout(self._desc_host)
        self._desc_layout.setContentsMargins(0, 0, 0, 0)
        self._desc_host.hide()

        self._scroll = QScrollArea()
        self._scroll.setObjectName("inspectorScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        self._body = QWidget()
        self._body.setObjectName("inspectorBody")
        self._sections = QVBoxLayout(self._body)
        self._sections.setContentsMargins(0, 0, 0, 0)
        self._sections.setSpacing(10)
        self._scroll.setWidget(self._body)

        self._footer_host = QWidget()
        self._footer_host.setObjectName("inspectorFooterHost")
        self._footer_layout = QVBoxLayout(self._footer_host)
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._footer_host.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(heading)
        layout.addWidget(self._coord_label)
        layout.addWidget(self._terrain_host)
        layout.addWidget(self._desc_host)
        layout.addWidget(self._scroll)
        layout.addWidget(self._footer_host)
        layout.addStretch(1)

    def apply_height_budget(self, max_h: int) -> int:
        self.setFixedHeight(max_h)
        return max_h

    def has_selection(self) -> bool:
        return self._has_selection

    def clear_selection(self) -> None:
        self._has_selection = False
        self._loading = False
        self._server_error = ""
        self._server_details = None
        self._local_tile = None
        self._local_paths = []
        self._local_edge = None
        self._coord_label.clear()
        self._clear_host(self._terrain_layout)
        self._terrain_host.hide()
        self._clear_host(self._desc_layout)
        self._desc_host.hide()
        self._clear_host(self._footer_layout)
        self._footer_host.hide()
        self._clear_sections()
        self._scroll.show()
        self._scroll.setFixedHeight(0)
        self._notify_layout_changed()

    def set_coord(self, q: int, r: int) -> None:
        self._has_selection = True
        self._coord_label.setText(f"Hex ({q}, {r})")

    def set_inspection(
        self,
        *,
        tile: dict | None,
        path_segments: list[dict],
        edge: dict | None,
    ) -> None:
        self._local_tile = tile
        self._local_paths = path_segments
        self._local_edge = edge
        self._rebuild()

    def set_details_loading(self) -> None:
        self._loading = True
        self._server_error = ""
        self._rebuild()

    def set_server_details(self, details: dict | None, *, error: str = "") -> None:
        self._loading = False
        self._server_error = error
        self._server_details = details
        self._rebuild()

    def _rebuild(self) -> None:
        self._clear_host(self._terrain_layout)
        self._terrain_host.hide()
        self._clear_host(self._desc_layout)
        self._desc_host.hide()
        self._clear_sections()
        self._clear_host(self._footer_layout)
        self._footer_host.hide()
        self._scroll.setFixedHeight(0)

        if self._loading:
            self._add_banner("Loading details…", level="info")
            self._scroll.show()
            self._fit_scroll_to_content()
            self._notify_layout_changed()
            return

        if self._server_error:
            self._add_banner(self._server_error, level="error")
            self._scroll.show()
            self._fit_scroll_to_content()
            self._notify_layout_changed()
            return

        server = self._server_details or {}
        tile = self._local_tile
        paths = self._local_paths
        edge = self._local_edge

        has_terrain = bool(tile and tile.get("terrain"))
        has_desc = bool(tile and tile.get("description", {}).get("text", "").strip())
        has_path = len(paths) > 0
        has_edge = bool(edge and int(edge.get("edges", 0)))
        has_any = has_terrain or has_desc or has_path or has_edge

        if has_terrain:
            stype = tile["terrain"].get("type", "")
            self._terrain_layout.addWidget(build_terrain_header(stype, server.get("terrain")))
            self._terrain_host.show()

        conn_rows = connection_row_count(paths, edge if has_edge else None)
        has_connections = has_path or has_edge

        if has_desc:
            text = tile["description"].get("text", "").strip()
            self._desc_layout.addWidget(build_description_card(text, server.get("description")))
            self._desc_host.show()

        if not has_any:
            self._add_empty_state(server)
            self._scroll.show()
            self._fit_scroll_to_content()

        if has_connections:
            self._sections.addWidget(
                build_connections_section(
                    paths,
                    edge if has_edge else None,
                    server.get("paths") or [],
                    server.get("edge"),
                    row_count=conn_rows,
                )
            )

        if has_connections:
            self._scroll.show()
            self._scroll.setFixedHeight(connections_scroll_height(conn_rows))
        else:
            self._scroll.hide()
            self._scroll.setFixedHeight(0)

        footer = build_footer_card(server, has_any=has_any)
        if footer is not None:
            self._footer_layout.addWidget(footer)
            self._footer_host.show()

        self._notify_layout_changed()

    def _fit_scroll_to_content(self) -> None:
        self._body.adjustSize()
        self._scroll.setFixedHeight(max(self._body.sizeHint().height(), 1))

    def _notify_layout_changed(self) -> None:
        self.adjustSize()
        parent = self.parent()
        if parent is not None and hasattr(parent, "reposition_panels"):
            parent.reposition_panels()

    @staticmethod
    def _clear_host(lay: QVBoxLayout) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_empty_state(self, server: dict) -> None:
        if server.get("terrain") or server.get("description"):
            message = "No terrain or description on this hex."
        else:
            message = "Empty hex — nothing placed yet."
        self._add_banner(message, level="info")

    def _add_banner(self, text: str, *, level: str = "info") -> None:
        lbl = QLabel(text)
        lbl.setObjectName("inspectorBanner")
        lbl.setProperty("level", level)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._polish(lbl)
        self._sections.addWidget(lbl)

    def _clear_sections(self) -> None:
        while self._sections.count():
            item = self._sections.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    @staticmethod
    def _polish(widget: QLabel) -> None:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
