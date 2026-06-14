from typing import Protocol

from PyQt6.QtCore import QObject

from controllers.session.paint_actions import PaintActions
from controllers.session.path_actions import PathActions
from controllers.session.undo_replay import UndoReplay
from controllers.map_sync_controller import MapSyncController
from models.map.edit_history import EditHistory
from models.map.local_map_state import LocalMapState
from models.map.tool_ids import TOOL_SELECT

class _MapViewPort(Protocol):
    def active_tool(self) -> str: ...
    def refresh_inspector(self, q: int, r: int) -> None: ...
    def apply_path_segment(self, path_id: str, waypoints: list, color: str) -> None: ...
    def remove_path(self, path_id: str) -> None: ...
    def apply_edge_tiles(self, tiles: list) -> None: ...
    def path_by_id(self, path_id: str) -> dict | None: ...
    def hovered_erase_component(self) -> str | None: ...
    def hovered_path_id(self) -> str | None: ...
    def hovered_edge(self) -> object: ...
    def show_error(self, message: str) -> None: ...
    def prompt_description(self, q: int, r: int) -> None: ...
    def selected_terrain(self) -> str | None: ...

class MapSessionController(QObject):
    def __init__(
        self,
        map_sync: MapSyncController,
        history: EditHistory,
        map_view: _MapViewPort,
        map_state: LocalMapState,
    ) -> None:
        super().__init__()
        self._map_sync = map_sync
        self._history = history
        self._map_view = map_view
        self._state = map_state
        self._inspector_coord: tuple[int, int] | None = None

        self._paint_actions = PaintActions(self)
        self._path_actions = PathActions(self)
        self._undo_replay = UndoReplay(self)

    def set_inspector_coord(self, coord: tuple[int, int] | None) -> None:
        self._inspector_coord = coord

    def clear_state(self) -> None:
        self._history.clear()
        self._path_actions.clear_path_state()
        self._inspector_coord = None

    def handle_editor_error(self, message: str) -> None:
        self._path_actions.handle_editor_error(message)

    def handle_hex_paint(self, q: int, r: int) -> None:
        self._paint_actions.handle_hex_paint(q, r)

    def handle_edge_painted(self, q: int, r: int, edge_index: int, color: str) -> None:
        self._paint_actions.handle_edge_painted(q, r, edge_index, color)

    def handle_map_edges_changed(self, map_id: str, tiles: list) -> None:
        self._paint_actions.handle_map_edges_changed(map_id, tiles)

    def handle_description_submitted(self, q: int, r: int, text: str) -> None:
        self._paint_actions.handle_description_submitted(q, r, text)

    def handle_path_drawn(self, waypoints: list, color: str) -> None:
        self._path_actions.handle_path_drawn(waypoints, color)

    def handle_map_path_added(
        self, map_id: str, path_id: str, waypoints: list, color: str
    ) -> None:
        self._path_actions.handle_map_path_added(map_id, path_id, waypoints, color)

    def handle_map_path_removed(self, map_id: str, path_id: str) -> None:
        self._path_actions.handle_map_path_removed(map_id, path_id)

    def undo(self) -> None:
        self._undo_replay.undo()

    def redo(self) -> None:
        self._undo_replay.redo()

    def _record_history(self, action: dict) -> None:
        self._history.record(action)

    def _refresh_inspector_if_open(self) -> None:
        if self._inspector_coord is None or self._map_view.active_tool() != TOOL_SELECT:
            return
        q, r = self._inspector_coord
        self._map_view.refresh_inspector(q, r)

    def _terrain_type_at(self, q: int, r: int) -> str | None:
        return self._state.terrain_type_at(q, r)

    def _description_text_at(self, q: int, r: int) -> str | None:
        text = self._state.description_text(q, r).strip()
        return text or None

    def _edge_snapshot(self, q: int, r: int) -> dict | None:
        return self._state.edge_snapshot(q, r)

    @staticmethod
    def _copy_waypoints(waypoints: list) -> list[list[int]]:
        result: list[list[int]] = []
        for waypoint in waypoints:
            if not isinstance(waypoint, (list, tuple)) or len(waypoint) < 2:
                continue
            result.append([int(waypoint[0]), int(waypoint[1])])
        return result
