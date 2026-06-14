from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from models.inspector_format import format_tile_record_lines

def build_footer_card(server: dict, *, has_any: bool) -> QWidget | None:
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
        return card

    if has_any and not tile_meta:
        lbl = QLabel("Not saved as a tile on the server.")
        lbl.setObjectName("inspectorFooterNote")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    return None
