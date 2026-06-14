from uuid import uuid4

from models.geometry import _segment_key, is_valid_polyline

class PathActions:
    def __init__(self, controller) -> None:
        self._controller = controller
        self.pending_local_path_id: str | None = None
        self.awaiting_path_add = False
        self.pending_path_history: dict | None = None

    def has_pending(self) -> bool:
        return bool(self.pending_path_history)

    def clear_path_state(self) -> None:
        self.pending_path_history = None
        self.awaiting_path_add = False
        self.pending_local_path_id = None

    def handle_editor_error(self, message: str) -> None:
        c = self._controller
        if self.awaiting_path_add and self.pending_local_path_id:
            c._map_view.remove_path(self.pending_local_path_id)
            self.pending_local_path_id = None
            self.awaiting_path_add = False
        self.pending_path_history = None
        c._map_view.show_error(message)

    def handle_path_drawn(self, waypoints: list, color: str) -> None:
        c = self._controller
        if not c._map_sync.can_edit or not is_valid_polyline(waypoints):
            return
        action = {
            "kind": "path",
            "op": "add",
            "waypoints": c._copy_waypoints(waypoints),
            "color": color,
            "path_ids": [],
        }
        if not c._history.replaying:
            self._start_path_history(action, push_when_complete=True)
        temp_id = f"__local_{uuid4().hex[:8]}"
        self.pending_local_path_id = temp_id
        self.awaiting_path_add = True
        c._map_view.apply_path_segment(temp_id, waypoints, color)
        c._map_sync.add_path(waypoints, color)

    def handle_map_path_added(
        self, map_id: str, path_id: str, waypoints: list, color: str
    ) -> None:
        c = self._controller
        if map_id != c._map_sync.open_map_id:
            return
        c._refresh_inspector_if_open()
        self.awaiting_path_add = False
        if self.pending_local_path_id:
            c._map_view.remove_path(self.pending_local_path_id)
            self.pending_local_path_id = None
        c._map_view.apply_path_segment(path_id, waypoints, color)
        self._track_pending_path_history(path_id, waypoints, color)

    def handle_map_path_removed(self, map_id: str, path_id: str) -> None:
        if map_id != self._controller._map_sync.open_map_id:
            return
        self._controller._map_view.remove_path(path_id)

    def add_path_for_history(self, action: dict) -> None:
        c = self._controller
        waypoints = c._copy_waypoints(action.get("waypoints", []))
        color = action.get("color", "")
        if not color or not is_valid_polyline(waypoints):
            return
        action["path_ids"] = []
        self._start_path_history(action, push_when_complete=False)
        c._map_sync.add_path(waypoints, color)

    def _start_path_history(self, action: dict, *, push_when_complete: bool) -> None:
        c = self._controller
        expected_keys = self._path_segment_keys(action.get("waypoints", []))
        if not expected_keys:
            return
        self.pending_path_history = {
            "action": action,
            "push": push_when_complete,
            "expected_keys": expected_keys,
            "seen_keys": set(),
            "ids": [],
            "existing_ids": set(c._state.path_ids()),
            "map_id": c._map_sync.open_map_id,
        }

    def _track_pending_path_history(
        self, path_id: str, waypoints: list, color: str
    ) -> None:
        c = self._controller
        pending = self.pending_path_history
        if pending is None or not path_id:
            return
        if pending.get("map_id") != c._map_sync.open_map_id:
            self.pending_path_history = None
            return
        action = pending["action"]
        if color != action.get("color"):
            return
        segment_keys = self._path_segment_keys(waypoints)
        if len(segment_keys) != 1:
            return
        segment_key = next(iter(segment_keys))
        if (
            segment_key not in pending["expected_keys"]
            or segment_key in pending["seen_keys"]
        ):
            return
        pending["seen_keys"].add(segment_key)
        if path_id not in pending["existing_ids"] and path_id not in pending["ids"]:
            pending["ids"].append(path_id)
        if len(pending["seen_keys"]) < len(pending["expected_keys"]):
            return
        action["path_ids"] = list(pending["ids"])
        self.pending_path_history = None
        if pending["push"] and action["path_ids"]:
            c._record_history(action)

    @staticmethod
    def _path_segment_keys(
        waypoints: list,
    ) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        coords = [
            (int(waypoint[0]), int(waypoint[1]))
            for waypoint in waypoints
            if isinstance(waypoint, (list, tuple)) and len(waypoint) >= 2
        ]
        return {
            _segment_key(start, end)
            for start, end in zip(coords, coords[1:])
            if start != end
        }
