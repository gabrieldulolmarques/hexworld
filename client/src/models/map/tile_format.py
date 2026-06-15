from models.geometry import Coord
from models.path_constants import DEFAULT_PATH_COLOR

def tile_from_server(payload: dict) -> dict | None:
    if not payload.get("terrain") and not payload.get("description"):
        return None
    tile: dict = {}
    terrain = payload.get("terrain")
    if terrain:
        tile["terrain"] = {"type": terrain.get("type", "")}
    description = payload.get("description")
    if description:
        tile["description"] = {"text": description.get("text", "")}
    return tile

def paths_from_server(paths: list) -> list[dict]:
    return [
        {
            "id": r.get("id", ""),
            "waypoints": r.get("waypoints", []),
            "color": r.get("color", DEFAULT_PATH_COLOR),
        }
        for r in paths
        if r.get("waypoints") and len(r["waypoints"]) >= 2
    ]

def edges_from_server(tiles: list) -> list[dict]:
    result: list[dict] = []
    for tile in tiles:
        q, r = tile.get("q"), tile.get("r")
        edges = int(tile.get("edges", 0) or 0)
        if q is None or r is None or edges <= 0:
            continue
        result.append(
            {
                "q": int(q),
                "r": int(r),
                "edges": edges & 0b111111,
                "color": tile.get("color", DEFAULT_PATH_COLOR),
            }
        )
    return result

def tiles_from_server(tiles: list[dict]) -> tuple[dict[Coord, dict], dict[Coord, str]]:
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
    return {
        "id": state.get("map_id", ""),
        "name": state.get("name", ""),
        "role": state.get("role", "viewer"),
        "member_count": state.get("member_count", 0),
    }
