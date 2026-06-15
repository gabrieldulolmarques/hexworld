from models.path_constants import DEFAULT_PATH_COLOR

class UndoReplay:
    def __init__(self, controller) -> None:
        self._controller = controller

    def undo(self) -> None:
        c = self._controller
        if (
            not c._map_sync.can_edit
            or not c._history.can_undo
            or c._path_actions.has_pending()
        ):
            return
        action = c._history.undo()
        if action is None:
            return
        if not self._history_action_is_current(action, undo=True):
            c._history.redo()
            c._map_view.show_error(
                "Cannot undo because this change is no longer current."
            )
            return
        self._apply_history_action(action, undo=True)

    def redo(self) -> None:
        c = self._controller
        if (
            not c._map_sync.can_edit
            or not c._history.can_redo
            or c._path_actions.has_pending()
        ):
            return
        action = c._history.redo()
        if action is None:
            return
        if not self._history_action_is_current(action, undo=False):
            c._history.undo()
            c._map_view.show_error(
                "Cannot redo because this change is no longer current."
            )
            return
        self._apply_history_action(action, undo=False)

    def _history_action_is_current(self, action: dict, *, undo: bool) -> bool:
        c = self._controller
        kind = action.get("kind")
        if kind == "terrain":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return c._terrain_type_at(q, r) == expected
        if kind == "description":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return c._description_text_at(q, r) == expected
        if kind == "edge":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return self._same_edge_state(c._edge_snapshot(q, r), expected)
        if kind == "path":
            return self._path_action_is_current(action, undo=undo)
        return False

    def _apply_history_action(self, action: dict, *, undo: bool) -> None:
        c = self._controller
        c._history.replaying = True
        try:
            kind = action.get("kind")
            if kind == "terrain":
                self._apply_terrain_history(action, undo=undo)
            elif kind == "description":
                self._apply_description_history(action, undo=undo)
            elif kind == "edge":
                self._apply_edge_history(action, undo=undo)
            elif kind == "path":
                self._apply_path_history(action, undo=undo)
        finally:
            c._history.replaying = False

    def _apply_terrain_history(self, action: dict, *, undo: bool) -> None:
        c = self._controller
        q, r = int(action["q"]), int(action["r"])
        value = action.get("before") if undo else action.get("after")
        if value:
            c._map_sync.set_terrain(q, r, value)
        else:
            c._map_sync.remove_terrain(q, r)

    def _apply_description_history(self, action: dict, *, undo: bool) -> None:
        c = self._controller
        q, r = int(action["q"]), int(action["r"])
        value = action.get("before") if undo else action.get("after")
        if value:
            c._map_sync.set_description(q, r, value)
        else:
            c._map_sync.remove_description(q, r)

    def _apply_edge_history(self, action: dict, *, undo: bool) -> None:
        q, r = int(action["q"]), int(action["r"])
        target = action.get("before") if undo else action.get("after")
        self._restore_edge_state(q, r, target)

    def _apply_path_history(self, action: dict, *, undo: bool) -> None:
        c = self._controller
        remove = (action.get("op") == "add" and undo) or (
            action.get("op") == "remove" and not undo
        )
        if remove:
            for path_id in list(action.get("path_ids", [])):
                c._map_sync.remove_path(path_id)
        else:
            c._path_actions.add_path_for_history(action)

    def _restore_edge_state(self, q: int, r: int, target: dict | None) -> None:
        c = self._controller
        current = c._edge_snapshot(q, r)
        current_edges = int(current["edges"]) if current else 0
        target_edges = int(target["edges"]) if target else 0
        target_color = target.get("color", DEFAULT_PATH_COLOR) if target else DEFAULT_PATH_COLOR
        for edge_index in range(6):
            if target_edges & (1 << edge_index):
                c._map_sync.set_edge(q, r, edge_index, target_color)
        for edge_index in range(6):
            bit = 1 << edge_index
            if current_edges & bit and not target_edges & bit:
                c._map_sync.remove_edge(q, r, edge_index)

    def _path_action_is_current(self, action: dict, *, undo: bool) -> bool:
        op = action.get("op")
        if op == "add":
            return (
                self._path_ids_exist(action)
                if undo
                else self._path_ids_are_absent(action)
            )
        if op == "remove":
            return (
                self._path_ids_are_absent(action)
                if undo
                else self._path_ids_exist(action)
            )
        return False

    def _path_ids_exist(self, action: dict) -> bool:
        c = self._controller
        path_ids = list(action.get("path_ids", []))
        if not path_ids:
            return False
        color = action.get("color")
        for path_id in path_ids:
            path = c._state.path_by_id(path_id)
            if path is None or path.get("color") != color:
                return False
        return True

    def _path_ids_are_absent(self, action: dict) -> bool:
        c = self._controller
        path_ids = list(action.get("path_ids", []))
        if not path_ids:
            return False
        return all(c._state.path_by_id(path_id) is None for path_id in path_ids)

    @staticmethod
    def _same_edge_state(left: dict | None, right: dict | None) -> bool:
        if left is None or right is None:
            return left is None and right is None
        return int(left.get("edges", 0) or 0) == int(
            right.get("edges", 0) or 0
        ) and left.get("color") == right.get("color")
