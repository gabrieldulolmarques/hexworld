from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models.inspector_format import edge_summary, format_editor_meta
from models.path_constants import DEFAULT_PATH_COLOR

_CONNECTION_SLOT_H = 58
_CONNECTIONS_CHROME_H = 52

def _editor_meta(component: dict | None) -> str:
    if not component:
        return ""
    return format_editor_meta(
        author=component.get("author", ""),
        created_at=component.get("created_at", ""),
        updated_at=component.get("updated_at", ""),
    )

def connection_row_count(segments: list[dict], edge: dict | None) -> int:
    colors = {segment.get("color", DEFAULT_PATH_COLOR) for segment in segments}
    rows = len(colors)
    if edge and int(edge.get("edges", 0)):
        rows += 1
    return rows

def connections_scroll_height(row_count: int) -> int:
    if row_count <= 0:
        return 0
    return _CONNECTIONS_CHROME_H + row_count * _CONNECTION_SLOT_H

def build_connections_section(
    segments: list[dict],
    edge: dict | None,
    server_paths: list[dict],
    server_edge: dict | None,
    *,
    row_count: int,
) -> QFrame:
    card = QFrame()
    card.setObjectName("inspectorConnectionsSection")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(10)

    title_lbl = QLabel("CONNECTIONS")
    title_lbl.setObjectName("fieldLabel")
    lay.addWidget(title_lbl)

    if segments:
        _append_path_rows(lay, segments, server_paths)

    if edge and int(edge.get("edges", 0)):
        mask = int(edge.get("edges", 0))
        color = edge.get("color", DEFAULT_PATH_COLOR)
        count, labels = edge_summary(mask)
        _append_connection_row(
            lay,
            color,
            f"Edges: {labels}" if count else "Edges",
            meta=_editor_meta(server_edge),
        )

    return card

def _append_path_rows(
    lay: QVBoxLayout,
    segments: list[dict],
    server_paths: list[dict],
) -> None:
    by_color: dict[str, list[dict]] = {}
    for segment in segments:
        color = segment.get("color", DEFAULT_PATH_COLOR)
        by_color.setdefault(color, []).append(segment)

    server_by_id = {r.get("id", ""): r for r in server_paths}

    for color, color_segments in by_color.items():
        count = len(color_segments)
        label = (
            "One path segment on this hex"
            if count == 1
            else f"{count} path segments on this hex"
        )
        metas: list[str] = []
        seen: set[str] = set()
        pending = False
        for segment in color_segments:
            path_id = segment.get("path_id", "")
            server_row = server_by_id.get(path_id)
            meta = _editor_meta(server_row)
            if meta and meta not in seen:
                seen.add(meta)
                metas.append(meta)
            elif path_id.startswith("__local_"):
                pending = True
        if pending and "Not synced with the server yet." not in metas:
            metas.append("Not synced with the server yet.")
        _append_connection_row(lay, color, label, meta=metas[0] if metas else "")

def _append_connection_row(
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
