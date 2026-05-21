"""Convert server tile payloads (RF09 / RF17) to HexCanvas tile dicts."""

from geometry import Coord


def tile_from_server(payload: dict) -> dict | None:
    """Return canvas tile data, or None if the hex should be cleared."""
    if not payload.get("structure") and not payload.get("roads") and not payload.get(
        "description"
    ):
        return None
    tile: dict = {}
    structure = payload.get("structure")
    if structure:
        tile["structure"] = {"type": structure.get("type", "")}
    description = payload.get("description")
    if description:
        tile["description"] = {"text": description.get("text", "")}
    roads = payload.get("roads") or []
    if roads:
        tile["road"] = {"color": roads[0].get("color", "#5ea500"), "id": roads[0].get("id", "")}
    return tile


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
