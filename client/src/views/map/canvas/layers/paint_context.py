from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QPainter

from models.geometry import Coord

@dataclass
class PaintContext:
    painter: QPainter
    origin: tuple[float, float]
    hex_size: float
    tiles: dict[Coord, dict]
    paths: list[dict]
    edges: dict[Coord, dict]
    extra_hexes: set[Coord]
    include_transient: bool
    minimap: bool
    selected: Coord | None
    hover: Coord | None
    hover_component: str | None
    erase_mode: bool
    path_preview: list[Coord]
    path_mode: bool = False
    path_submode: str = "path"
    path_color: str = ""
    hover_path_id: str | None = None
    hover_edge: tuple[Coord, int] | None = None
    current_path: list[Coord] | None = None
    path_hint_next_hexes: set[Coord] | None = None
