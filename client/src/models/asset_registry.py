"""
Asset registry for map tiles.

Directory layout: assets/map/{biome}/{biome}_{nn}_{key}.png
structure.type in the DB = filename stem = '{biome}_{nn}_{key}'
  e.g. 'greenlands_11_village', 'forest_14_village', 'deadlands_00_empty'

Each terrain biome (except forest and mountain) includes a biome-tinted
``{biome}_00_empty`` tile. There is no shared empty biome folder.

Access: REGISTRY.pixmap('greenlands_11_village', hex_size) → flat-top QPixmap
"""
import math
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPixmap

from geometry import hex_vertices

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "map"

_BIOME_ORDER = (
    "deadlands",
    "drylands",
    "forest",
    "greenlands",
    "icelands",
    "mountain",
    "sandlands",
)


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
        ordered = [b for b in _BIOME_ORDER if b in self._by_biome]
        extra = sorted(b for b in self._by_biome if b not in _BIOME_ORDER)
        return ordered + extra

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
            self._cache[cache_key] = _hex_fitted_pixmap(QPixmap(str(info.path)), size)
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


def _hex_fitted_pixmap(source: QPixmap, hex_size: int) -> QPixmap:
    diam = hex_size * 2
    if source.isNull():
        empty = QPixmap(diam, diam)
        empty.fill(Qt.GlobalColor.transparent)
        return empty

    short_axis = round(math.sqrt(3) * hex_size)
    target_w = diam
    target_h = short_axis
    ratio_mode = (
        Qt.AspectRatioMode.KeepAspectRatio
        if source.width() >= source.height()
        else Qt.AspectRatioMode.KeepAspectRatioByExpanding
    )

    scaled = source.scaled(
        target_w, target_h,
        ratio_mode,
        Qt.TransformationMode.SmoothTransformation,
    )
    if scaled.width() != target_w or scaled.height() != target_h:
        ox = max(0, (scaled.width() - target_w) // 2)
        oy = max(0, (scaled.height() - target_h) // 2)
        scaled = scaled.copy(ox, oy, min(target_w, scaled.width()), min(target_h, scaled.height()))

    path = QPainterPath()
    verts = hex_vertices(diam / 2, diam / 2, hex_size)
    path.moveTo(*verts[0])
    for x, y in verts[1:]:
        path.lineTo(x, y)
    path.closeSubpath()

    result = QPixmap(diam, diam)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipPath(path)
    painter.drawPixmap(
        (diam - scaled.width()) // 2,
        (diam - scaled.height()) // 2,
        scaled,
    )
    painter.end()
    return result


REGISTRY = AssetRegistry()
