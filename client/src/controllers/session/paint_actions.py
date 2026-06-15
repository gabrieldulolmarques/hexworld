from models.map.tool_ids import TOOL_DESCRIPTION, TOOL_ERASE, TOOL_TERRAIN
from models.path_constants import DEFAULT_PATH_COLOR

class PaintActions:
    def __init__(self, controller) -> None:
        self._controller = controller

    def handle_hex_paint(self, q: int, r: int) -> None:
        c = self._controller
        if not c._map_sync.can_edit:
            return
        tool = c._map_view.active_tool()
        if tool == TOOL_TERRAIN:
            terrain = c._map_view.selected_terrain()
            if not terrain:
                c._map_view.show_error("Select a terrain from the palette first.")
                return
            before = c._terrain_type_at(q, r)
            if before == terrain:
                return
            c._record_history(
                {
                    "kind": "terrain",
                    "q": q,
                    "r": r,
                    "before": before,
                    "after": terrain,
                }
            )
            c._map_sync.set_terrain(q, r, terrain)
        elif tool == TOOL_DESCRIPTION:
            c._map_view.prompt_description(q, r)
        elif tool == TOOL_ERASE:
            component = c._map_view.hovered_erase_component()
            if component == "terrain":
                before = c._terrain_type_at(q, r)
                if before is None:
                    return
                c._record_history(
                    {
                        "kind": "terrain",
                        "q": q,
                        "r": r,
                        "before": before,
                        "after": None,
                    }
                )
                c._map_sync.remove_terrain(q, r)
            elif component == "path":
                path_id = c._map_view.hovered_path_id()
                if path_id:
                    path = c._map_view.path_by_id(path_id)
                    if path is not None:
                        c._record_history(
                            {
                                "kind": "path",
                                "op": "remove",
                                "waypoints": c._copy_waypoints(
                                    path.get("waypoints", [])
                                ),
                                "color": path.get("color", DEFAULT_PATH_COLOR),
                                "path_ids": [path_id],
                            }
                        )
                    c._map_sync.remove_path(path_id)
            elif component == "edge":
                edge = c._map_view.hovered_edge()
                if edge:
                    coord, edge_index = edge
                    before = c._edge_snapshot(coord[0], coord[1])
                    if before is None:
                        return
                    bit = 1 << edge_index
                    before_edges = int(before["edges"])
                    if not before_edges & bit:
                        return
                    after_edges = before_edges & ~bit
                    after = (
                        {"edges": after_edges, "color": before.get("color", DEFAULT_PATH_COLOR)}
                        if after_edges
                        else None
                    )
                    c._record_history(
                        {
                            "kind": "edge",
                            "q": coord[0],
                            "r": coord[1],
                            "before": before,
                            "after": after,
                        }
                    )
                    c._map_sync.remove_edge(coord[0], coord[1], edge_index)
            elif component == "description":
                before = c._description_text_at(q, r)
                if before is None:
                    return
                c._record_history(
                    {
                        "kind": "description",
                        "q": q,
                        "r": r,
                        "before": before,
                        "after": None,
                    }
                )
                c._map_sync.remove_description(q, r)

    def handle_edge_painted(self, q: int, r: int, edge_index: int, color: str) -> None:
        c = self._controller
        if not c._map_sync.can_edit:
            return
        before = c._edge_snapshot(q, r)
        before_edges = int(before["edges"]) if before else 0
        bit = 1 << edge_index
        after = {"edges": before_edges | bit, "color": color}
        if before_edges & bit and before and before.get("color") == color:
            return
        c._record_history(
            {
                "kind": "edge",
                "q": q,
                "r": r,
                "before": before,
                "after": after,
            }
        )
        c._map_sync.set_edge(q, r, edge_index, color)

    def handle_map_edges_changed(self, map_id: str, tiles: list) -> None:
        c = self._controller
        if map_id != c._map_sync.open_map_id:
            return
        c._map_view.apply_edge_tiles(tiles)
        c._refresh_inspector_if_open()

    def handle_description_submitted(self, q: int, r: int, text: str) -> None:
        c = self._controller
        if not c._map_sync.can_edit:
            return
        text = text.strip()
        if not text:
            return
        before = c._description_text_at(q, r)
        if before == text:
            return
        c._record_history(
            {
                "kind": "description",
                "q": q,
                "r": r,
                "before": before,
                "after": text,
            }
        )
        c._map_sync.set_description(q, r, text)
