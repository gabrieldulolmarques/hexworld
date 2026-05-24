from pathlib import Path

from PyQt6.QtCore import QTimer

from controllers.auth_controller import AuthController
from controllers.map_controller import MapController
from controllers.transport_worker import TransportWorker
from models.preferences import Preferences
from models.session import Session
from geometry import is_valid_polyline
from models.tile_format import (
    inner_edges_from_server,
    map_state_for_view,
    roads_from_server,
    tiles_from_server,
)
from transport.client import Client
from views.auth_view import AuthView
from views.home_view import HomeView
from views.main_view import MainView
from views.map.constants import (
    TOOL_DESCRIPTION,
    TOOL_ERASE,
    TOOL_SELECT,
    TOOL_STRUCTURE,
)
from views.map_view import MapView

_RECONNECT_DELAY_MS = 5000
_HISTORY_LIMIT = 200


class ClientController:
    def __init__(self, main_view: MainView) -> None:
        self.main_view = main_view
        self.auth_view = AuthView()
        self.home_view = HomeView()
        self.map_view = MapView()

        main_view.stack.addWidget(self.auth_view)
        main_view.stack.addWidget(self.home_view)
        main_view.stack.addWidget(self.map_view)

        self.client = Client()
        self.transport_worker = TransportWorker(self.client)
        self.transport_worker.start()

        self.session = Session()
        self._stopping = False
        self._pending_local_road_id: str | None = None
        self._awaiting_road_add = False
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._history_replaying = False
        self._pending_road_history: dict | None = None
        self._current_map_name = ""
        self._inspector_coord: tuple[int, int] | None = None

        self.preferences = Preferences()
        self._restore_preferences()

        self.auth = AuthController(self.transport_worker, self.session, self.preferences)
        self.maps = MapController(self.transport_worker, self.session)
        self._connect_signals()

        if self.session.is_authenticated():
            self.auth.validate_session()

    def _connect_signals(self) -> None:
        # Auth
        self.auth_view.request_login.connect(self.auth.login)
        self.auth_view.request_register.connect(self.auth.register)
        self.home_view.request_logout.connect(self.auth.logout)
        self.auth.login_success.connect(self._show_home)
        self.auth.session_restored.connect(self._show_home)
        self.auth.register_success.connect(self._on_register_success)
        self.auth.logged_out.connect(self._show_auth)
        self.auth.session_error.connect(self._show_auth)
        self.auth.loading.connect(self._on_auth_loading)
        self.auth.error.connect(self._on_auth_error)

        # Maps — home
        self.home_view.request_create_map.connect(self.maps.create_map)
        self.home_view.request_join_map.connect(self.maps.join_map)
        self.home_view.request_dissociate_map.connect(self.maps.dissociate_map)
        self.home_view.request_delete_map.connect(self.maps.delete_map)
        self.home_view.request_open_map.connect(self._on_open_map)
        self.maps.maps_loaded.connect(self.home_view.set_maps)
        self.maps.map_created.connect(self._on_map_created)
        self.maps.map_joined.connect(self._on_map_joined)
        self.maps.map_removed.connect(self.home_view.remove_map)
        self.maps.create_error.connect(self.home_view.show_create_error)
        self.maps.join_error.connect(self.home_view.show_join_error)
        self.maps.error.connect(lambda msg: self.home_view.show_message(msg, level="error"))
        self.maps.session_error.connect(self._show_auth)
        self.maps.loading.connect(self._on_map_loading)
        self.maps.map_member_count_changed.connect(self.home_view.update_map_member_count)
        self.maps.map_member_count_changed.connect(self._on_map_member_count_changed)
        self.maps.map_role_changed.connect(self.home_view.update_map_role)

        # Maps — editor
        self.map_view.request_back.connect(self._on_map_back)
        self.maps.map_state_loaded.connect(self._on_map_state_loaded)
        self.maps.map_presence_changed.connect(self._on_map_presence_changed)
        self.maps.map_tile_changed.connect(self._on_map_tile_changed)
        self.maps.map_road_added.connect(self._on_map_road_added)
        self.maps.map_road_removed.connect(self._on_map_road_removed)
        self.maps.map_inner_edges_changed.connect(self._on_map_inner_edges_changed)
        self.maps.map_editor_error.connect(self._on_map_editor_error)
        self.map_view.hex_paint_clicked.connect(self._on_hex_paint_clicked)
        self.map_view.road_drawn.connect(self._on_road_drawn)
        self.map_view.inner_edge_painted.connect(self._on_inner_edge_painted)
        self.map_view.description_submitted.connect(self._on_description_submitted)
        self.map_view.undo_requested.connect(self._undo)
        self.map_view.redo_requested.connect(self._redo)
        self.map_view.export_requested.connect(self._on_export_requested)
        self.map_view.export_submitted.connect(self._on_export_submitted)
        self.map_view.hex_selected.connect(self._on_hex_selected_for_inspector)
        self.maps.cell_details_loaded.connect(self._on_cell_details_loaded)
        self.maps.cell_details_error.connect(self._on_cell_details_error)

        self.transport_worker.finished.connect(self._on_worker_finished)

    # ------------------------------------------------------------------
    # Auth callbacks
    # ------------------------------------------------------------------

    def _on_auth_loading(self, loading: bool) -> None:
        if self.main_view.stack.currentWidget() is self.home_view:
            self.home_view.set_loading(loading)
        else:
            self.auth_view.set_loading(loading)

    def _on_auth_error(self, message: str) -> None:
        if self.main_view.stack.currentWidget() is self.home_view:
            self.home_view.show_message(message, level="error")
        else:
            self.auth_view.show_message(message, level="error")

    def _on_register_success(self) -> None:
        self.auth_view.show_register_success()

    def _show_home(self, username: str) -> None:
        self.home_view.set_user(username)
        self.home_view.go_home()
        self.main_view.stack.setCurrentWidget(self.home_view)
        self.maps.get_maps()

    def _show_auth(self) -> None:
        self._restore_preferences()
        self.auth_view.reset()
        self.main_view.stack.setCurrentWidget(self.auth_view)

    def _restore_preferences(self) -> None:
        username, remember = self.preferences.load()
        self.auth_view.set_login_defaults(username, remember)

    # ------------------------------------------------------------------
    # Map callbacks
    # ------------------------------------------------------------------

    def _on_map_loading(self, loading: bool) -> None:
        self.home_view.set_create_loading(loading)
        self.home_view.set_join_loading(loading)

    def _on_map_created(self, data: dict) -> None:
        self.home_view.add_map(data)
        self.home_view.go_home()

    def _on_map_joined(self, data: dict) -> None:
        self.home_view.add_map(data)
        self.home_view.go_home()

    def _on_open_map(self, map_id: str) -> None:
        self.main_view.stack.setCurrentWidget(self.map_view)
        self.maps.open_map(map_id)

    def _on_map_back(self) -> None:
        self._clear_history()
        self._current_map_name = ""
        self._inspector_coord = None
        self.maps.close_map()
        self.home_view.go_home()
        self.main_view.stack.setCurrentWidget(self.home_view)

    def _on_map_state_loaded(self, state: dict) -> None:
        self._clear_history()
        canvas_tiles, tile_ids = tiles_from_server(state.get("tiles", []))
        for (q, r), tile_id in tile_ids.items():
            self.maps.remember_tile(q, r, tile_id)
        view_data = map_state_for_view(state)
        self._current_map_name = view_data.get("name", "")
        self.map_view.set_map(view_data)
        self.map_view.set_tiles(canvas_tiles)
        roads = roads_from_server(state.get("roads", []))
        self.map_view.canvas.set_roads(roads)
        inner_edges = inner_edges_from_server(state.get("inner_edges", []))
        self.map_view.canvas.set_inner_edges(inner_edges)
        self.map_view.set_online_users(state.get("online_users", []))
        self.map_view.update_member_count(view_data.get("member_count", 0))

    def _on_map_member_count_changed(self, map_id: str, count: int) -> None:
        if map_id == self.maps.open_map_id:
            self.map_view.update_member_count(count)

    def _on_map_presence_changed(self, map_id: str, online_users: list) -> None:
        if map_id != self.maps.open_map_id:
            return
        self.map_view.set_online_users(online_users)

    def _on_hex_selected_for_inspector(self, q: int, r: int) -> None:
        if self.maps.open_map_id is None:
            return
        self._inspector_coord = (q, r)
        self.map_view.set_inspector_details_loading()
        self.maps.fetch_cell_details(q, r)

    def _on_cell_details_loaded(self, q: int, r: int, details: dict) -> None:
        if self._inspector_coord != (q, r):
            return
        self.map_view.set_inspector_server_details(details)

    def _on_cell_details_error(self, q: int, r: int, message: str) -> None:
        if self._inspector_coord != (q, r):
            return
        self.map_view.set_inspector_server_details(None, error=message)

    def _on_map_tile_changed(
        self, map_id: str, q: int, r: int, payload: dict,
    ) -> None:
        if map_id != self.maps.open_map_id:
            return
        tile_id = payload.get("tile_id")
        if tile_id:
            self.maps.remember_tile(q, r, tile_id)
        self.map_view.apply_server_tile(q, r, payload)
        if self._inspector_coord == (q, r) and self.map_view.active_tool() == TOOL_SELECT:
            self.map_view.refresh_inspector(q, r)
            self.maps.fetch_cell_details(q, r)

    def _on_map_editor_error(self, message: str) -> None:
        if self._awaiting_road_add and self._pending_local_road_id:
            self.map_view.canvas.remove_road_by_id(self._pending_local_road_id)
            self._pending_local_road_id = None
            self._awaiting_road_add = False
        self._pending_road_history = None
        self.home_view.show_message(message, level="error")

    def _on_road_drawn(self, waypoints: list, color: str) -> None:
        if not self.maps.can_edit:
            return
        from uuid import uuid4

        if not is_valid_polyline(waypoints):
            return
        action = {
            "kind": "road",
            "op": "add",
            "waypoints": self._copy_waypoints(waypoints),
            "color": color,
            "road_ids": [],
        }
        if not self._history_replaying:
            self._start_road_history(action, push_when_complete=True)
        temp_id = f"__local_{uuid4().hex[:8]}"
        self._pending_local_road_id = temp_id
        self._awaiting_road_add = True
        self.map_view.canvas.apply_road(temp_id, waypoints, color)
        self.maps.add_road(waypoints, color)

    def _on_map_road_added(self, map_id: str, road_id: str, waypoints: list, color: str) -> None:
        if map_id != self.maps.open_map_id:
            return
        self._refresh_inspector_if_open()
        self._awaiting_road_add = False
        if self._pending_local_road_id:
            self.map_view.canvas.remove_road_by_id(self._pending_local_road_id)
            self._pending_local_road_id = None
        self.map_view.canvas.apply_road(road_id, waypoints, color)
        self._track_pending_road_history(road_id, waypoints, color)

    def _on_map_road_removed(self, map_id: str, road_id: str) -> None:
        if map_id != self.maps.open_map_id:
            return
        self.map_view.canvas.remove_road_by_id(road_id)

    def _on_inner_edge_painted(self, q: int, r: int, edge_index: int, color: str) -> None:
        if not self.maps.can_edit:
            return
        before = self._inner_edge_snapshot(q, r)
        before_edges = int(before["edges"]) if before else 0
        bit = 1 << edge_index
        after = {"edges": before_edges | bit, "color": color}
        if before_edges & bit and before and before.get("color") == color:
            return
        self._record_history({
            "kind": "inner_edge",
            "q": q,
            "r": r,
            "before": before,
            "after": after,
        })
        self.maps.set_inner_edge(q, r, edge_index, color)

    def _on_map_inner_edges_changed(self, map_id: str, cells: list) -> None:
        if map_id != self.maps.open_map_id:
            return
        for cell in cells:
            self.map_view.canvas.apply_inner_edge_cell(cell)
        self._refresh_inspector_if_open()

    def _refresh_inspector_if_open(self) -> None:
        if self._inspector_coord is None:
            return
        if self.map_view.active_tool() != TOOL_SELECT:
            return
        q, r = self._inspector_coord
        self.map_view.refresh_inspector(q, r)

    def _on_hex_paint_clicked(self, q: int, r: int) -> None:
        if not self.maps.can_edit:
            return
        tool = self.map_view.active_tool()
        if tool == TOOL_STRUCTURE:
            structure = self.map_view.selected_structure()
            if not structure:
                self.home_view.show_message(
                    "Select a structure from the palette first.",
                    level="error",
                )
                return
            before = self._structure_type_at(q, r)
            if before == structure:
                return
            self._record_history({
                "kind": "structure",
                "q": q,
                "r": r,
                "before": before,
                "after": structure,
            })
            self.maps.set_structure(q, r, structure)
        elif tool == TOOL_DESCRIPTION:
            self.map_view.prompt_description(q, r)
        elif tool == TOOL_ERASE:
            component = self.map_view.canvas.hovered_erase_component()
            if component == "structure":
                before = self._structure_type_at(q, r)
                if before is None:
                    return
                self._record_history({
                    "kind": "structure",
                    "q": q,
                    "r": r,
                    "before": before,
                    "after": None,
                })
                self.maps.remove_structure(q, r)
            elif component == "road":
                road_id = self.map_view.canvas.hovered_road_id()
                if road_id:
                    road = self.map_view.canvas.road_by_id(road_id)
                    if road is not None:
                        self._record_history({
                            "kind": "road",
                            "op": "remove",
                            "waypoints": self._copy_waypoints(road.get("waypoints", [])),
                            "color": road.get("color", "#5ea500"),
                            "road_ids": [road_id],
                        })
                    self.maps.remove_road(road_id)
            elif component == "inner_edge":
                edge = self.map_view.canvas.hovered_inner_edge()
                if edge:
                    coord, edge_index = edge
                    before = self._inner_edge_snapshot(coord[0], coord[1])
                    if before is None:
                        return
                    bit = 1 << edge_index
                    before_edges = int(before["edges"])
                    if not before_edges & bit:
                        return
                    after_edges = before_edges & ~bit
                    after = (
                        {"edges": after_edges, "color": before.get("color", "#5ea500")}
                        if after_edges else None
                    )
                    self._record_history({
                        "kind": "inner_edge",
                        "q": coord[0],
                        "r": coord[1],
                        "before": before,
                        "after": after,
                    })
                    self.maps.remove_inner_edge(coord[0], coord[1], edge_index)
            elif component == "description":
                before = self._description_text_at(q, r)
                if before is None:
                    return
                self._record_history({
                    "kind": "description",
                    "q": q,
                    "r": r,
                    "before": before,
                    "after": None,
                })
                self.maps.remove_description(q, r)

    def _on_description_submitted(self, q: int, r: int, text: str) -> None:
        if not self.maps.can_edit:
            return
        text = text.strip()
        if not text:
            return
        before = self._description_text_at(q, r)
        if before == text:
            return
        self._record_history({
            "kind": "description",
            "q": q,
            "r": r,
            "before": before,
            "after": text,
        })
        self.maps.set_description(q, r, text)

    # ------------------------------------------------------------------
    # Undo / redo
    # ------------------------------------------------------------------

    def _undo(self) -> None:
        if not self.maps.can_edit or not self._undo_stack or self._pending_road_history:
            return
        action = self._undo_stack.pop()
        if not self._history_action_is_current(action, undo=True):
            self.home_view.show_message(
                "Cannot undo because this change is no longer current.",
                level="error",
            )
            return
        self._apply_history_action(action, undo=True)
        self._redo_stack.append(action)
        if len(self._redo_stack) > _HISTORY_LIMIT:
            self._redo_stack.pop(0)

    def _redo(self) -> None:
        if not self.maps.can_edit or not self._redo_stack or self._pending_road_history:
            return
        action = self._redo_stack.pop()
        if not self._history_action_is_current(action, undo=False):
            self.home_view.show_message(
                "Cannot redo because this change is no longer current.",
                level="error",
            )
            return
        self._apply_history_action(action, undo=False)
        self._undo_stack.append(action)
        if len(self._undo_stack) > _HISTORY_LIMIT:
            self._undo_stack.pop(0)

    def _record_history(self, action: dict) -> None:
        if self._history_replaying:
            return
        self._undo_stack.append(action)
        if len(self._undo_stack) > _HISTORY_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _clear_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._pending_road_history = None

    def _history_action_is_current(self, action: dict, *, undo: bool) -> bool:
        kind = action.get("kind")
        if kind == "structure":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return self._structure_type_at(q, r) == expected
        if kind == "description":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return self._description_text_at(q, r) == expected
        if kind == "inner_edge":
            q, r = int(action["q"]), int(action["r"])
            expected = action.get("after") if undo else action.get("before")
            return self._same_inner_edge_state(self._inner_edge_snapshot(q, r), expected)
        if kind == "road":
            return self._road_action_is_current(action, undo=undo)
        return False

    def _apply_history_action(self, action: dict, *, undo: bool) -> None:
        self._history_replaying = True
        try:
            kind = action.get("kind")
            if kind == "structure":
                self._apply_structure_history(action, undo=undo)
            elif kind == "description":
                self._apply_description_history(action, undo=undo)
            elif kind == "inner_edge":
                self._apply_inner_edge_history(action, undo=undo)
            elif kind == "road":
                self._apply_road_history(action, undo=undo)
        finally:
            self._history_replaying = False

    def _apply_structure_history(self, action: dict, *, undo: bool) -> None:
        q, r = int(action["q"]), int(action["r"])
        value = action.get("before") if undo else action.get("after")
        if value:
            self.maps.set_structure(q, r, value)
        else:
            self.maps.remove_structure(q, r)

    def _apply_description_history(self, action: dict, *, undo: bool) -> None:
        q, r = int(action["q"]), int(action["r"])
        value = action.get("before") if undo else action.get("after")
        if value:
            self.maps.set_description(q, r, value)
        else:
            self.maps.remove_description(q, r)

    def _apply_inner_edge_history(self, action: dict, *, undo: bool) -> None:
        q, r = int(action["q"]), int(action["r"])
        target = action.get("before") if undo else action.get("after")
        self._restore_inner_edge_state(q, r, target)

    def _apply_road_history(self, action: dict, *, undo: bool) -> None:
        remove = (action.get("op") == "add" and undo) or (
            action.get("op") == "remove" and not undo
        )
        if remove:
            for road_id in list(action.get("road_ids", [])):
                self.maps.remove_road(road_id)
        else:
            self._add_road_for_history(action)

    def _add_road_for_history(self, action: dict) -> None:
        waypoints = self._copy_waypoints(action.get("waypoints", []))
        color = action.get("color", "")
        if not color or not is_valid_polyline(waypoints):
            return
        action["road_ids"] = []
        self._start_road_history(action, push_when_complete=False)
        self.maps.add_road(waypoints, color)

    def _restore_inner_edge_state(self, q: int, r: int, target: dict | None) -> None:
        current = self._inner_edge_snapshot(q, r)
        current_edges = int(current["edges"]) if current else 0
        target_edges = int(target["edges"]) if target else 0
        target_color = target.get("color", "#5ea500") if target else "#5ea500"
        for edge_index in range(6):
            if target_edges & (1 << edge_index):
                self.maps.set_inner_edge(q, r, edge_index, target_color)
        for edge_index in range(6):
            bit = 1 << edge_index
            if current_edges & bit and not target_edges & bit:
                self.maps.remove_inner_edge(q, r, edge_index)

    def _start_road_history(self, action: dict, *, push_when_complete: bool) -> None:
        expected_keys = self._road_segment_keys(action.get("waypoints", []))
        if not expected_keys:
            return
        self._pending_road_history = {
            "action": action,
            "push": push_when_complete,
            "expected_keys": expected_keys,
            "seen_keys": set(),
            "ids": [],
            "existing_ids": set(self.map_view.canvas.road_ids()),
        }

    def _track_pending_road_history(self, road_id: str, waypoints: list, color: str) -> None:
        pending = self._pending_road_history
        if pending is None or not road_id:
            return
        action = pending["action"]
        if color != action.get("color"):
            return
        segment_keys = self._road_segment_keys(waypoints)
        if len(segment_keys) != 1:
            return
        segment_key = next(iter(segment_keys))
        if segment_key not in pending["expected_keys"] or segment_key in pending["seen_keys"]:
            return
        pending["seen_keys"].add(segment_key)
        if road_id not in pending["existing_ids"] and road_id not in pending["ids"]:
            pending["ids"].append(road_id)
        if len(pending["seen_keys"]) < len(pending["expected_keys"]):
            return
        action["road_ids"] = list(pending["ids"])
        self._pending_road_history = None
        if pending["push"] and action["road_ids"]:
            self._record_history(action)

    def _structure_type_at(self, q: int, r: int) -> str | None:
        tile = self.map_view.canvas.tile_at(q, r) or {}
        structure = tile.get("structure") or {}
        return structure.get("type") or None

    def _description_text_at(self, q: int, r: int) -> str | None:
        text = self.map_view.canvas.description_text(q, r).strip()
        return text or None

    def _inner_edge_snapshot(self, q: int, r: int) -> dict | None:
        cell = self.map_view.canvas.inner_edge_cell(q, r)
        if not cell:
            return None
        edges = int(cell.get("edges", 0) or 0) & 0b111111
        if not edges:
            return None
        return {"edges": edges, "color": cell.get("color", "#5ea500")}

    @staticmethod
    def _same_inner_edge_state(left: dict | None, right: dict | None) -> bool:
        if left is None or right is None:
            return left is None and right is None
        return (
            int(left.get("edges", 0) or 0) == int(right.get("edges", 0) or 0)
            and left.get("color") == right.get("color")
        )

    def _road_action_is_current(self, action: dict, *, undo: bool) -> bool:
        op = action.get("op")
        if op == "add":
            return self._road_ids_exist(action) if undo else self._road_ids_are_absent(action)
        if op == "remove":
            return self._road_ids_are_absent(action) if undo else self._road_ids_exist(action)
        return False

    def _road_ids_exist(self, action: dict) -> bool:
        road_ids = list(action.get("road_ids", []))
        if not road_ids:
            return False
        color = action.get("color")
        for road_id in road_ids:
            road = self.map_view.canvas.road_by_id(road_id)
            if road is None or road.get("color") != color:
                return False
        return True

    def _road_ids_are_absent(self, action: dict) -> bool:
        road_ids = list(action.get("road_ids", []))
        if not road_ids:
            return False
        return all(self.map_view.canvas.road_by_id(road_id) is None for road_id in road_ids)

    @staticmethod
    def _copy_waypoints(waypoints: list) -> list[list[int]]:
        result: list[list[int]] = []
        for wp in waypoints:
            if not isinstance(wp, (list, tuple)) or len(wp) < 2:
                continue
            result.append([int(wp[0]), int(wp[1])])
        return result

    @staticmethod
    def _road_segment_keys(waypoints: list) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        coords = [
            (int(wp[0]), int(wp[1]))
            for wp in waypoints
            if isinstance(wp, (list, tuple)) and len(wp) >= 2
        ]
        keys: set[tuple[tuple[int, int], tuple[int, int]]] = set()
        for start, end in zip(coords, coords[1:]):
            if start == end:
                continue
            keys.add((start, end) if start <= end else (end, start))
        return keys

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export_requested(self) -> None:
        self.map_view.open_export_dialog(str(Path.home() / self._default_export_filename()))

    def _on_export_submitted(self, path: str) -> None:
        export_path = self._normalize_export_path(Path(path))
        self.map_view.set_export_busy(True)
        if self._save_canvas_export(export_path):
            self.map_view.show_export_success(str(export_path))
        else:
            self.map_view.show_export_error(
                "The full map image could not be generated or saved.",
            )

    def _default_export_filename(self) -> str:
        name = self._current_map_name.strip() or "hexworld-map"
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in name)
        safe = "-".join(part for part in safe.split("-") if part)
        return f"{safe or 'hexworld-map'}.png"

    @staticmethod
    def _normalize_export_path(path: Path) -> Path:
        if path.suffix.lower() == ".png":
            return path
        if path.suffix:
            return Path(f"{path}.png")
        return path.with_suffix(".png")

    def _save_canvas_export(self, path: Path) -> bool:
        image = self.map_view.canvas.export_full_map_image()
        if image.isNull():
            return False
        return image.save(str(path), "PNG")

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _on_worker_finished(self) -> None:
        if self._stopping:
            return
        QTimer.singleShot(_RECONNECT_DELAY_MS, self._restart_worker)

    def _restart_worker(self) -> None:
        if self._stopping:
            return
        self.transport_worker.reset()
        self.transport_worker.start()

    def stop(self) -> None:
        self._stopping = True
        self.transport_worker.stop()
        self.client.stop()
