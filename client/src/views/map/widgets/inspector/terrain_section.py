from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from models.asset_registry import REGISTRY
from models.inspector_format import format_editor_meta, terrain_display

_TERRAIN_THUMB = 48

def _editor_meta(component: dict | None) -> str:
    if not component:
        return ""
    return format_editor_meta(
        author=component.get("author", ""),
        created_at=component.get("created_at", ""),
        updated_at=component.get("updated_at", ""),
    )

def build_terrain_header(stype: str, server_terrain: dict | None) -> QFrame:
    title, biome = terrain_display(stype)
    card = QFrame()
    card.setObjectName("inspectorTerrainHeader")
    row = QHBoxLayout(card)
    row.setContentsMargins(12, 10, 12, 10)
    row.setSpacing(12)

    thumb = QLabel()
    thumb.setObjectName("inspectorPreview")
    thumb.setFixedSize(_TERRAIN_THUMB, _TERRAIN_THUMB)
    thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    px = REGISTRY.pixmap(stype, _TERRAIN_THUMB * 0.75)
    if px and not px.isNull():
        thumb.setPixmap(
            px.scaled(
                _TERRAIN_THUMB,
                _TERRAIN_THUMB,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
        )
    row.addWidget(thumb)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    name_lbl = QLabel(title)
    name_lbl.setObjectName("inspectorTerrainName")
    text_col.addWidget(name_lbl)
    if biome:
        biome_lbl = QLabel(biome)
        biome_lbl.setObjectName("inspectorTerrainBiome")
        text_col.addWidget(biome_lbl)
    meta = _editor_meta(server_terrain)
    if meta:
        meta_lbl = QLabel(meta)
        meta_lbl.setObjectName("inspectorMetaLine")
        meta_lbl.setWordWrap(True)
        text_col.addWidget(meta_lbl)
    row.addLayout(text_col, 1)

    return card
