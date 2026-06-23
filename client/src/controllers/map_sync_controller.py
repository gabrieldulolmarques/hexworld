from PyQt6.QtCore import QObject, pyqtSignal

from models.session import Session
from rmi.worker import RemoteWorker

_ERROR_MESSAGES = {
    "unexpected_error": "Unexpected server error.",
    "not_editor": "You need editor access to change this map.",
    "not_member": "You are not a member of this map.",
    "invalid_path": "Paths must use adjacent hexes without reusing a segment.",
}

class MapSyncController(QObject):
    loading = pyqtSignal(bool)
    error = pyqtSignal(str)
    map_presence_changed = pyqtSignal(str, list)
    map_tile_changed = pyqtSignal(str, int, int, dict)
    map_path_added = pyqtSignal(str, str, list, str)
    map_path_removed = pyqtSignal(str, str)
    map_edges_changed = pyqtSignal(str, list)
    map_state_loaded = pyqtSignal(dict)
    editor_error = pyqtSignal(str)
    tile_details_loaded = pyqtSignal(int, int, dict)
    tile_details_error = pyqtSignal(int, int, str)
    session_error = pyqtSignal()

    def __init__(self, worker: RemoteWorker, session: Session) -> None:
        super().__init__()
        self._worker = worker
        self._session = session
        self._open_map_id: str | None = None
        self._tile_ids: dict[tuple[int, int], str] = {}
        self._map_role: str = "viewer"
        worker.evt_tile_changed.connect(self._on_evt_tile_changed)
        worker.evt_path_added.connect(self._on_evt_path_added)
        worker.evt_path_removed.connect(self._on_evt_path_removed)
        worker.evt_edge_changed.connect(self._on_evt_edge_changed)
        worker.evt_presence_changed.connect(self._on_evt_presence_changed)
        worker.evt_ownership_transferred.connect(self._on_evt_ownership_transferred)

    def open_map(self, map_id: str) -> None:
        self._open_map_id = map_id
        self._tile_ids.clear()
        call = self._worker.open_map(map_id)
        call.succeeded.connect(self._on_state_loaded)
        call.failed.connect(self._on_open_failed)

    def close_map(self) -> None:
        if self._open_map_id:
            self._worker.close_map()
        self._open_map_id = None
        self._tile_ids.clear()

    @property
    def open_map_id(self) -> str | None:
        return self._open_map_id

    @property
    def can_edit(self) -> bool:
        return self._map_role in ("owner", "editor")

    def remember_tile(self, q: int, r: int, tile_id: str) -> None:
        self._tile_ids[(q, r)] = tile_id

    def get_tile_details(self, q: int, r: int) -> None:
        if not self._open_map_id:
            self.tile_details_error.emit(q, r, "No map is open.")
            return
        tile_id = self._tile_ids.get((q, r))
        if not tile_id:
            self.tile_details_loaded.emit(q, r, {})
            return
        call = self._worker.get_tile_details(tile_id)
        call.succeeded.connect(
            lambda details, q=q, r=r: self.tile_details_loaded.emit(q, r, details)
        )
        call.failed.connect(
            lambda code, q=q, r=r: self._on_tile_details_failed(q, r, code)
        )

    def set_terrain(self, q: int, r: int, terrain_type: str) -> None:
        if not self._open_map_id or not terrain_type:
            return
        call = self._worker.set_terrain(q, r, terrain_type)
        call.succeeded.connect(self._on_tile_op_ok)
        call.failed.connect(self._on_editor_failed)

    def set_description(self, q: int, r: int, text: str) -> None:
        if not self._open_map_id:
            return
        text = text.strip()
        if not text:
            return
        call = self._worker.set_description(q, r, text)
        call.succeeded.connect(self._on_tile_op_ok)
        call.failed.connect(self._on_editor_failed)

    def add_path(self, waypoints: list, color: str) -> None:
        if not self._open_map_id or not color or len(waypoints) < 2:
            return
        call = self._worker.add_path(waypoints, color)
        call.succeeded.connect(lambda data: self._emit_path_segments(data))
        call.failed.connect(self._on_editor_failed)

    def remove_terrain(self, q: int, r: int) -> None:
        tile_id = self._tile_ids.get((q, r))
        if not self._open_map_id or not tile_id:
            return
        self._worker.remove_terrain(tile_id).failed.connect(self._on_editor_failed)

    def remove_path(self, path_id: str) -> None:
        if not self._open_map_id or not path_id:
            return
        self._worker.remove_path(path_id).failed.connect(self._on_editor_failed)

    def remove_description(self, q: int, r: int) -> None:
        tile_id = self._tile_ids.get((q, r))
        if not self._open_map_id or not tile_id:
            return
        self._worker.remove_description(tile_id).failed.connect(self._on_editor_failed)

    def set_edge(self, q: int, r: int, edge_index: int, color: str) -> None:
        if not self._open_map_id or not color:
            return
        call = self._worker.set_edge(q, r, edge_index, color)
        call.succeeded.connect(self._on_edge_op_ok)
        call.failed.connect(self._on_editor_failed)

    def remove_edge(self, q: int, r: int, edge_index: int) -> None:
        if not self._open_map_id:
            return
        call = self._worker.remove_edge(q, r, edge_index)
        call.succeeded.connect(self._on_edge_op_ok)
        call.failed.connect(self._on_editor_failed)

    # ---- call results ----

    def _on_state_loaded(self, state: dict) -> None:
        self._map_role = state.get("role", "viewer")
        self.map_state_loaded.emit(state)

    def _on_open_failed(self, code: str) -> None:
        if code == "invalid_token":
            self.session_error.emit()
            return
        self.editor_error.emit(_message(code))

    def _on_tile_op_ok(self, data: dict) -> None:
        tile_id = data.get("tile_id")
        q, r = data.get("q"), data.get("r")
        if (
            self._open_map_id
            and tile_id is not None
            and q is not None
            and r is not None
        ):
            self.remember_tile(int(q), int(r), tile_id)

    def _on_edge_op_ok(self, data: dict) -> None:
        tiles = data.get("tiles", [])
        if self._open_map_id and tiles:
            self.map_edges_changed.emit(self._open_map_id, tiles)

    def _on_editor_failed(self, code: str) -> None:
        if code == "invalid_token":
            self.session_error.emit()
            return
        self.editor_error.emit(_message(code))

    def _on_tile_details_failed(self, q: int, r: int, code: str) -> None:
        if code == "invalid_token":
            self.session_error.emit()
            return
        self.tile_details_error.emit(q, r, _message(code))

    # ---- server-pushed events ----

    def _on_evt_tile_changed(self, map_id: str, q: int, r: int, tile: dict) -> None:
        self.map_tile_changed.emit(map_id, q, r, tile)

    def _on_evt_path_added(self, map_id: str, path: dict) -> None:
        self._emit_path_segments(path, map_id=map_id)

    def _on_evt_path_removed(self, map_id: str, path_id: str) -> None:
        self.map_path_removed.emit(map_id, path_id)

    def _on_evt_edge_changed(self, map_id: str, tiles: list) -> None:
        self.map_edges_changed.emit(map_id, tiles)

    def _on_evt_presence_changed(self, map_id: str, online_users: list) -> None:
        self.map_presence_changed.emit(map_id, online_users)

    def _on_evt_ownership_transferred(self, map_id: str, new_owner_id: str) -> None:
        if new_owner_id == self._session.user_id:
            self._map_role = "owner"

    def _emit_path_segments(self, data: dict, *, map_id: str | None = None) -> None:
        target_map_id = map_id or self._open_map_id
        if not target_map_id:
            return
        segments = data.get("segments")
        if segments is None:
            segments = [data]
        for segment in segments:
            path_id = segment.get("path_id", "")
            waypoints = segment.get("waypoints", [])
            color = segment.get("color", "")
            if path_id and waypoints and color:
                self.map_path_added.emit(target_map_id, path_id, waypoints, color)

def _message(code: str) -> str:
    return _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
