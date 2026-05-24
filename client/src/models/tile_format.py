"""Convert server tile payloads (RF09 / RF17) to HexCanvas tile dicts.

Roads are now map-level segments (RF13), not tile-level components.
tile_from_server only handles structure and description.
"""

from geometry import Coord


def tile_from_server(payload: dict) -> dict | None:
    """Return canvas tile data, or None if the hex should be cleared."""
    if not payload.get("structure") and not payload.get("description"):
        return None
    tile: dict = {}
    structure = payload.get("structure")
    if structure:
        tile["structure"] = {"type": structure.get("type", "")}
    description = payload.get("description")
    if description:
        tile["description"] = {"text": description.get("text", "")}
    return tile


def roads_from_server(roads: list) -> list[dict]:
    """Normalize the road segment list from get_map_state into canvas dicts."""
    return [
        {
            "id": r.get("id", ""),
            "waypoints": r.get("waypoints", []),
            "color": r.get("color", "#5ea500"),
        }
        for r in roads
        if r.get("waypoints") and len(r["waypoints"]) >= 2
    ]


def inner_edges_from_server(cells: list) -> list[dict]:
    """Normalize persisted inner-edge masks from get_map_state."""
    result: list[dict] = []
    for cell in cells:
        q, r = cell.get("q"), cell.get("r")
        edges = int(cell.get("edges", 0) or 0)
        if q is None or r is None or edges <= 0:
            continue
        result.append({
            "q": int(q),
            "r": int(r),
            "edges": edges & 0b111111,
            "color": cell.get("color", "#5ea500"),
        })
    return result


def tiles_from_server(tiles: list[dict]) -> tuple[dict[Coord, dict], dict[Coord, str]]:
    """Build canvas tiles and coord → tile_id index from get_map_state tiles."""
    canvas_tiles: dict[Coord, dict] = {}
    tile_ids: dict[Coord, str] = {}
    for entry in tiles:
        q, r = entry.get("q"), entry.get("r")
        if q is None or r is None:
            continue
        coord = (int(q), int(r))
        tile_id = entry.get("tile_id")
        if tile_id:
            tile_ids[coord] = tile_id
        canvas = tile_from_server(entry)
        if canvas:
            canvas_tiles[coord] = canvas
    return canvas_tiles, tile_ids


def map_state_for_view(state: dict) -> dict:
    """Normalize get_map_state payload for MapView.set_map."""
    return {
        "id": state.get("map_id", ""),
        "name": state.get("name", ""),
        "role": state.get("role", "viewer"),
        "member_count": state.get("member_count", 0),
    }
