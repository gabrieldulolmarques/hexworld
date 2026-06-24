from PyQt6.QtCore import QObject, pyqtSignal

from models.session import Session
from sockets.worker import Worker
from sockets.messages import STATUS_ERROR
from sockets.protocol import request

_ERROR_MESSAGES = {
    "unexpected_error": "Unexpected server error.",
    "not_editor": "You need editor access to change this map.",
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

    def __init__(self, worker: Worker, session: Session) -> None:
        super().__init__()
        self._worker = worker
        self._session = session
        self._pending: set[str] = set()
        self._details_pending: dict[str, tuple[int, int]] = {}
        self._open_map_id: str | None = None
        self._tile_ids: dict[tuple[int, int], str] = {}
        self._map_role: str = "viewer"
        worker.response.connect(self._on_response)
        worker.event.connect(self._on_event)

    def open_map(self, map_id: str) -> None:
        self._open_map_id = map_id
        self._tile_ids.clear()
        self._send(
            request(
                "get_map_state",
                {"token": self._session.token, "map_id": map_id},
            ),
        )

    def close_map(self) -> None:
        if self._open_map_id:
            self._send(
                request(
                    "close_map",
                    {"token": self._session.token, "map_id": self._open_map_id},
                ),
            )
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
        request_frame = request(
            "get_tile_details",
            {
                "token": self._session.token,
                "map_id": self._open_map_id,
                "tile_id": tile_id,
            },
        )
        self._details_pending[request_frame["request_id"]] = (q, r)
        if not self._worker.submit(request_frame):
            self._details_pending.pop(request_frame["request_id"], None)
            self.tile_details_error.emit(q, r, _ERROR_MESSAGES["unexpected_error"])

    def set_terrain(self, q: int, r: int, terrain_type: str) -> None:
        if not self._open_map_id or not terrain_type:
            return
        self._send(
            request(
                "set_terrain",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "q": q,
                    "r": r,
                    "type": terrain_type,
                },
            ),
        )

    def add_path(self, waypoints: list, color: str) -> None:
        if not self._open_map_id or not color or len(waypoints) < 2:
            return
        self._send(
            request(
                "add_path",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "waypoints": waypoints,
                    "color": color,
                },
            ),
        )

    def remove_terrain(self, q: int, r: int) -> None:
        tile_id = self._tile_ids.get((q, r))
        if not self._open_map_id or not tile_id:
            return
        self._send(
            request(
                "remove_terrain",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "tile_id": tile_id,
                },
            ),
        )

    def remove_path(self, path_id: str) -> None:
        if not self._open_map_id or not path_id:
            return
        self._send(
            request(
                "remove_path",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "path_id": path_id,
                },
            ),
        )

    def set_edge(self, q: int, r: int, edge_index: int, color: str) -> None:
        if not self._open_map_id or not color:
            return
        self._send(
            request(
                "set_edge",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "q": q,
                    "r": r,
                    "edge_index": edge_index,
                    "color": color,
                },
            ),
        )

    def remove_edge(self, q: int, r: int, edge_index: int) -> None:
        if not self._open_map_id:
            return
        self._send(
            request(
                "remove_edge",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "q": q,
                    "r": r,
                    "edge_index": edge_index,
                },
            ),
        )

    def remove_description(self, q: int, r: int) -> None:
        tile_id = self._tile_ids.get((q, r))
        if not self._open_map_id or not tile_id:
            return
        self._send(
            request(
                "remove_description",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "tile_id": tile_id,
                },
            ),
        )

    def set_description(self, q: int, r: int, text: str) -> None:
        if not self._open_map_id:
            return
        text = text.strip()
        if not text:
            return
        self._send(
            request(
                "set_description",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "q": q,
                    "r": r,
                    "text": text,
                },
            ),
        )

    def _send(self, request: dict) -> None:
        self._pending.add(request["request_id"])
        if len(self._pending) == 1:
            self.loading.emit(True)
        if not self._worker.submit(request):
            self._pending.discard(request["request_id"])
            if not self._pending:
                self.loading.emit(False)
            self.error.emit(_ERROR_MESSAGES["unexpected_error"])

    def _on_response(self, response: dict) -> None:
        request_id = response.get("request_id", "")

        if request_id in self._details_pending:
            q, r = self._details_pending.pop(request_id)
            if response.get("status") == STATUS_ERROR:
                code = response.get("code", "")
                if code == "invalid_token":
                    self.session_error.emit()
                    return
                message = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
                self.tile_details_error.emit(q, r, message)
            else:
                self.tile_details_loaded.emit(q, r, response.get("data", {}))
            return

        if request_id not in self._pending:
            return
        self._pending.discard(request_id)
        if not self._pending:
            self.loading.emit(False)

        req_type = response.get("type", "")

        if response.get("status") == STATUS_ERROR:
            code = response.get("code", "")
            if code == "invalid_token":
                self.session_error.emit()
                return
            message = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
            if req_type in (
                "get_map_state",
                "set_terrain",
                "set_description",
                "add_path",
                "set_edge",
                "remove_edge",
                "remove_terrain",
                "remove_path",
                "remove_description",
            ):
                self.editor_error.emit(message)
            elif req_type == "close_map":
                pass
            else:
                self.error.emit(message)
            return

        data = response.get("data", {})
        match req_type:
            case "get_map_state":
                self._map_role = data.get("role", "viewer")
                self.map_state_loaded.emit(data)
            case "set_terrain" | "set_description":
                tile_id = data.get("tile_id")
                q, r = data.get("q"), data.get("r")
                if (
                    self._open_map_id
                    and tile_id is not None
                    and q is not None
                    and r is not None
                ):
                    self.remember_tile(int(q), int(r), tile_id)
            case "add_path":
                self._emit_path_segments(data)
            case "remove_terrain" | "remove_path" | "remove_description":
                pass
            case "set_edge" | "remove_edge":
                tiles = data.get("tiles", [])
                if self._open_map_id and tiles:
                    self.map_edges_changed.emit(self._open_map_id, tiles)
            case "close_map":
                pass

    def _on_event(self, evt: dict) -> None:
        evt_type = evt.get("type", "")
        map_id = evt.get("map_id", "")
        data = evt.get("data", {})

        if evt_type == "map_ownership_transferred":
            if data.get("new_owner_id") == self._session.user_id:
                self._map_role = "owner"
        elif evt_type in ("map_user_online", "map_user_offline"):
            self.map_presence_changed.emit(map_id, data.get("online_users", []))
        elif evt_type in (
            "terrain_set",
            "terrain_removed",
            "description_set",
            "description_removed",
        ):
            q, r = data.get("q"), data.get("r")
            if q is not None and r is not None:
                self.map_tile_changed.emit(map_id, int(q), int(r), data)
        elif evt_type == "path_added":
            self._emit_path_segments(data, map_id=map_id)
        elif evt_type == "path_removed":
            self.map_path_removed.emit(map_id, data.get("path_id", ""))
        elif evt_type == "edge_changed":
            self.map_edges_changed.emit(map_id, data.get("tiles", []))

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
