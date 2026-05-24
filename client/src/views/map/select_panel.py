"""Right floating card — hex inspector when a cell is selected."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from models.asset_registry import REGISTRY
from models.inspector_format import (
    format_editor_meta,
    format_tile_record_lines,
    inner_edge_summary,
    structure_display,
)
from styles.colors import GREEN_PRIMARY
from views.map.constants import SIDE_PANEL_W
from views.map.panel import MapPanel

_STRUCTURE_THUMB = 48
_DESC_MIN_HEIGHT = 180
_CONNECTION_SLOT_H = 58
_CONNECTIONS_CHROME_H = 52

_INSPECTOR_MARKDOWN_CSS = f"""
body, p, div, span, li, td, th, em, i {{
    color: #ffffff;
    font-size: 15px;
    line-height: 1.45;
}}
body {{ margin: 0; }}
p {{ margin: 6px 0; }}
h1, h2, h3 {{ color: #ffffff; margin: 12px 0 6px; font-weight: 600; }}
h1 {{ font-size: 1.35em; }}
h2 {{ font-size: 1.2em; }}
h3 {{ font-size: 1.05em; }}
ul, ol {{ margin: 6px 0; padding-left: 1.4em; }}
li {{ margin: 3px 0; }}
code, pre {{ color: #ffffff; background: #27272a; }}
code {{ padding: 1px 5px; border-radius: 4px; font-size: 0.92em; }}
pre {{ padding: 10px; border-radius: 6px; overflow-x: auto; }}
blockquote {{
    border-left: 3px solid {GREEN_PRIMARY};
    margin: 8px 0;
    padding: 4px 12px;
    color: #e4e4e7;
}}
a {{ color: #bbf7d0; text-decoration: none; }}
strong, b {{ color: #ffffff; font-weight: 600; }}
"""


class SelectPanel(MapPanel):
    def __init__(self) -> None:
        super().__init__("mapSelectPanel")
        self.setFixedWidth(SIDE_PANEL_W)
        self._has_selection = False
        self._loading = False
        self._server_error = ""
        self._server_details: dict | None = None
        self._local_tile: dict | None = None
        self._local_roads: list[dict] = []
        self._local_inner: dict | None = None

        heading = QLabel("INSPECTOR")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._coord_label = QLabel()
        self._coord_label.setObjectName("title")
        self._coord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._structure_host = QWidget()
        self._structure_host.setObjectName("inspectorStructureHost")
        self._structure_layout = QVBoxLayout(self._structure_host)
        self._structure_layout.setContentsMargins(0, 0, 0, 0)
        self._structure_host.hide()

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
        layout.addWidget(self._structure_host)
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
        self._local_roads = []
        self._local_inner = None
        self._coord_label.clear()
        self._clear_host(self._structure_layout)
        self._structure_host.hide()
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
        road_segments: list[dict],
        inner_edge: dict | None,
    ) -> None:
        self._local_tile = tile
        self._local_roads = road_segments
        self._local_inner = inner_edge
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
        self._clear_host(self._structure_layout)
        self._structure_host.hide()
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
        roads = self._local_roads
        inner_edge = self._local_inner

        has_structure = bool(tile and tile.get("structure"))
        has_desc = bool(tile and tile.get("description", {}).get("text", "").strip())
        has_road = len(roads) > 0
        has_inner = bool(inner_edge and int(inner_edge.get("edges", 0)))
        has_any = has_structure or has_desc or has_road or has_inner

        if has_structure:
            stype = tile["structure"].get("type", "")
            self._mount_structure_header(stype, server.get("structure"))
            self._structure_host.show()

        conn_rows = self._connection_row_count(roads, inner_edge if has_inner else None)
        has_connections = has_road or has_inner

        if has_desc:
            text = tile["description"].get("text", "").strip()
            meta = self._editor_meta(server.get("description"))
            self._mount_description(text, meta=meta)
            self._desc_host.show()

        if not has_any:
            self._add_empty_state(server)
            self._scroll.show()
            self._fit_scroll_to_content()

        if has_connections:
            self._add_connections_section(
                roads,
                inner_edge if has_inner else None,
                server.get("roads") or [],
                server.get("inner_edge"),
                row_count=conn_rows,
            )

        if has_connections:
            self._scroll.show()
            scroll_h = self._connections_scroll_height(conn_rows)
            self._scroll.setFixedHeight(scroll_h)
        else:
            self._scroll.hide()
            self._scroll.setFixedHeight(0)

        self._mount_footer(server, has_any=has_any)
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
    def _connection_row_count(
        segments: list[dict],
        inner_edge: dict | None,
    ) -> int:
        colors = {seg.get("color", "#5ea500") for seg in segments}
        rows = len(colors)
        if inner_edge and int(inner_edge.get("edges", 0)):
            rows += 1
        return rows

    @staticmethod
    def _connections_scroll_height(row_count: int) -> int:
        if row_count <= 0:
            return 0
        return _CONNECTIONS_CHROME_H + row_count * _CONNECTION_SLOT_H

    @staticmethod
    def _editor_meta(component: dict | None) -> str:
        if not component:
            return ""
        return format_editor_meta(
            author=component.get("author", ""),
            created_at=component.get("created_at", ""),
            updated_at=component.get("updated_at", ""),
        )

    @staticmethod
    def _clear_host(lay: QVBoxLayout) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _mount_structure_header(self, stype: str, server_structure: dict | None) -> None:
        title, biome = structure_display(stype)
        card = QFrame()
        card.setObjectName("inspectorStructureHeader")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        thumb = QLabel()
        thumb.setObjectName("inspectorPreview")
        thumb.setFixedSize(_STRUCTURE_THUMB, _STRUCTURE_THUMB)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = REGISTRY.pixmap(stype, _STRUCTURE_THUMB * 0.75)
        if px and not px.isNull():
            thumb.setPixmap(
                px.scaled(
                    _STRUCTURE_THUMB,
                    _STRUCTURE_THUMB,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        row.addWidget(thumb)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name_lbl = QLabel(title)
        name_lbl.setObjectName("inspectorStructureName")
        text_col.addWidget(name_lbl)
        if biome:
            biome_lbl = QLabel(biome)
            biome_lbl.setObjectName("inspectorStructureBiome")
            text_col.addWidget(biome_lbl)
        meta = self._editor_meta(server_structure)
        if meta:
            meta_lbl = QLabel(meta)
            meta_lbl.setObjectName("inspectorMetaLine")
            meta_lbl.setWordWrap(True)
            text_col.addWidget(meta_lbl)
        row.addLayout(text_col, 1)

        self._structure_layout.addWidget(card)

    def _mount_description(self, text: str, *, meta: str = "") -> None:
        card = QFrame()
        card.setObjectName("inspectorDescSection")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        title_lbl = QLabel("DESCRIPTION")
        title_lbl.setObjectName("fieldLabel")
        lay.addWidget(title_lbl)

        browser = QTextBrowser()
        browser.setObjectName("inspectorDescBrowser")
        browser.setOpenLinks(False)
        browser.setReadOnly(True)
        browser.setMinimumHeight(_DESC_MIN_HEIGHT)
        browser.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        palette = browser.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        browser.setPalette(palette)
        browser.document().setDefaultStyleSheet(_INSPECTOR_MARKDOWN_CSS)
        browser.setMarkdown(text)
        lay.addWidget(browser)

        if meta:
            meta_lbl = QLabel(meta)
            meta_lbl.setObjectName("inspectorDescMeta")
            meta_lbl.setWordWrap(True)
            lay.addWidget(meta_lbl)

        self._desc_layout.addWidget(card)

    def _mount_footer(self, server: dict, *, has_any: bool) -> None:
        tile_meta = server.get("tile")
        lines = (
            format_tile_record_lines(
                tile_meta.get("created_at", ""),
                tile_meta.get("updated_at", ""),
            )
            if tile_meta
            else []
        )

        if lines:
            card = QFrame()
            card.setObjectName("inspectorFooter")
            lay = QVBoxLayout(card)
            lay.setContentsMargins(12, 10, 12, 10)
            lay.setSpacing(4)
            title = QLabel("Saved on server")
            title.setObjectName("inspectorTileRecordTitle")
            lay.addWidget(title)
            for line in lines:
                lbl = QLabel(line)
                lbl.setObjectName("inspectorTileRecordLine")
                lbl.setWordWrap(True)
                lay.addWidget(lbl)
            self._footer_layout.addWidget(card)
            self._footer_host.show()
            return

        if has_any and not tile_meta:
            lbl = QLabel("Not saved as a tile on the server.")
            lbl.setObjectName("inspectorFooterNote")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._footer_layout.addWidget(lbl)
            self._footer_host.show()

    def _add_empty_state(self, server: dict) -> None:
        if server.get("structure") or server.get("description"):
            msg = "No structure or description on this hex."
        else:
            msg = "Empty hex — nothing placed yet."
        self._add_banner(msg, level="info")

    def _add_connections_section(
        self,
        segments: list[dict],
        inner_edge: dict | None,
        server_roads: list[dict],
        server_inner: dict | None,
        *,
        row_count: int,
    ) -> None:
        card = QFrame()
        card.setObjectName("inspectorConnectionsSection")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        title_lbl = QLabel("CONNECTIONS")
        title_lbl.setObjectName("fieldLabel")
        lay.addWidget(title_lbl)

        if segments:
            self._append_road_rows(lay, segments, server_roads)

        if inner_edge and int(inner_edge.get("edges", 0)):
            mask = int(inner_edge.get("edges", 0))
            color = inner_edge.get("color", "#5ea500")
            count, labels = inner_edge_summary(mask)
            self._append_connection_row(
                lay,
                color,
                f"Inner edges: {labels}" if count else "Inner edges",
                meta=self._editor_meta(server_inner),
            )

        self._sections.addWidget(card)

    def _append_road_rows(
        self,
        lay: QVBoxLayout,
        segments: list[dict],
        server_roads: list[dict],
    ) -> None:
        by_color: dict[str, list[dict]] = {}
        for seg in segments:
            color = seg.get("color", "#5ea500")
            by_color.setdefault(color, []).append(seg)

        server_by_id = {r.get("id", ""): r for r in server_roads}

        for color, segs in by_color.items():
            count = len(segs)
            label = (
                "One road segment on this hex"
                if count == 1
                else f"{count} road segments on this hex"
            )
            metas: list[str] = []
            seen: set[str] = set()
            pending = False
            for seg in segs:
                road_id = seg.get("road_id", "")
                server_row = server_by_id.get(road_id)
                meta = self._editor_meta(server_row)
                if meta and meta not in seen:
                    seen.add(meta)
                    metas.append(meta)
                elif road_id.startswith("__local_"):
                    pending = True
            if pending and "Not synced with the server yet." not in metas:
                metas.append("Not synced with the server yet.")
            meta_line = metas[0] if len(metas) == 1 else ""
            if len(metas) > 1:
                meta_line = metas[0]
            self._append_connection_row(lay, color, label, meta=meta_line)

    def _append_connection_row(
        self,
        lay: QVBoxLayout,
        color: str,
        text: str,
        *,
        meta: str = "",
    ) -> None:
        block = QWidget()
        block.setMinimumHeight(_CONNECTION_SLOT_H - 8)
        block_lay = QVBoxLayout(block)
        block_lay.setContentsMargins(0, 0, 0, 0)
        block_lay.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)
        swatch = QLabel()
        swatch.setFixedSize(18, 18)
        swatch.setStyleSheet(
            f"background-color: {color};"
            " border: 1px solid rgba(255,255,255,0.25);"
            " border-radius: 4px;",
        )
        row.addWidget(swatch)
        line = QLabel(text)
        line.setObjectName("inspectorValue")
        line.setWordWrap(True)
        row.addWidget(line, 1)
        block_lay.addLayout(row)

        if meta:
            meta_lbl = QLabel(meta)
            meta_lbl.setObjectName("inspectorMetaLine")
            meta_lbl.setWordWrap(True)
            meta_lbl.setContentsMargins(26, 0, 0, 0)
            block_lay.addWidget(meta_lbl)

        lay.addWidget(block)

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
