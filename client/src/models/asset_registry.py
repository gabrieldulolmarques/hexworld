"""
Asset registry for map tiles.

Directory layout: assets/map/{biome}/{biome}_{nn}_{key}.png
structure.type in the DB = filename stem = '{biome}_{nn}_{key}'
  e.g. 'greenlands_11_village', 'forest_14_village', 'deadlands_18_ruins'

Access: REGISTRY.pixmap('greenlands_11_village', hex_size) → clipped QPixmap
"""
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPixmap

from geometry import hex_vertices

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "map"


@dataclass(frozen=True)
class TileInfo:
    biome: str
    index: int
    key:   str    # e.g. "dead_trees"
    label: str    # e.g. "Dead Trees"
    stem:  str    # e.g. "deadlands_17_dead_trees"  (= structure.type)
    path:  Path


class AssetRegistry:
    def __init__(self) -> None:
        self._by_stem:  dict[str, TileInfo] = {}
        self._by_biome: dict[str, list[TileInfo]] = {}
        self._cache:    dict[tuple[str, int], QPixmap] = {}
        self._scan()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def biomes(self) -> list[str]:
        return sorted(self._by_biome)

    def tiles(self, biome: str) -> list[TileInfo]:
        return self._by_biome.get(biome, [])

    def tile(self, structure_type: str) -> TileInfo | None:
        return self._by_stem.get(structure_type)

    def pixmap(self, structure_type: str, hex_size: float) -> QPixmap | None:
        """structure_type = structure.type from the DB, e.g. 'greenlands_11_village'."""
        info = self._by_stem.get(structure_type)
        if info is None:
            return None
        size = round(hex_size)
        cache_key = (structure_type, size)
        if cache_key not in self._cache:
            self._cache[cache_key] = _hex_clipped_pixmap(QPixmap(str(info.path)), size)
        return self._cache[cache_key]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scan(self) -> None:
        if not _ASSETS_DIR.exists():
            return
        for biome_dir in sorted(_ASSETS_DIR.iterdir()):
            if not biome_dir.is_dir():
                continue
            biome = biome_dir.name
            tiles: list[TileInfo] = []
            for png in sorted(biome_dir.glob("*.png")):
                info = _parse_tile(biome, png)
                if info:
                    tiles.append(info)
                    self._by_stem[info.stem] = info
            if tiles:
                self._by_biome[biome] = tiles


def _parse_tile(biome: str, path: Path) -> TileInfo | None:
    stem = path.stem                        # e.g. "greenlands_11_village"
    prefix = f"{biome}_"
    if not stem.startswith(prefix):
        return None
    rest = stem[len(prefix):]               # "11_village"
    idx_str, _, key = rest.partition("_")
    if not idx_str.isdigit():
        return None
    label = key.replace("_", " ").title()
    return TileInfo(
        biome=biome,
        index=int(idx_str),
        key=key,
        label=label,
        stem=stem,
        path=path,
    )


def _hex_clipped_pixmap(source: QPixmap, hex_size: int) -> QPixmap:
    diam = hex_size * 2
    scaled = source.scaled(
        diam, diam,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    ox = (scaled.width()  - diam) // 2
    oy = (scaled.height() - diam) // 2
    scaled = scaled.copy(ox, oy, diam, diam)

    path = QPainterPath()
    verts = hex_vertices(diam / 2, diam / 2, hex_size - 1.5)
    path.moveTo(*verts[0])
    for x, y in verts[1:]:
        path.lineTo(x, y)
    path.closeSubpath()

    result = QPixmap(diam, diam)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return result


REGISTRY = AssetRegistry()
