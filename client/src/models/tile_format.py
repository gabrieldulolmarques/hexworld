"""Convert server tile payloads (RF09 / RF17) to HexCanvas tile dicts."""


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
        tile["road"] = {"color": roads[0].get("color", "#5ea500")}
    return tile
