from PyQt6.QtCore import QObject, pyqtSignal

from controllers.transport_worker import TransportWorker
from limits import MAX_MAP_NAME_LEN
from models.session import Session
from transport.protocol import request

_ERROR_MESSAGES = {
    "missing_fields":    "Missing fields.",
    "map_name_too_long": "Map name is too long.",
    "invalid_code":      "Invalid invite code.",
    "already_member":    "You are already a member of this map.",
    "map_full":          "This map is full (128 members max).",
    "not_member":        "You are not a member of this map.",
    "not_owner":         "Only the owner can delete this map.",
    "map_has_members":   "Remove all other members before deleting.",
    "use_delete":        "You are the only member — use Delete instead.",
    "unexpected_error":  "Unexpected server error.",
    "not_editor":        "You need editor access to change this map.",
    "invalid_path":      "Roads must use adjacent hexes without reusing a segment.",
}


class MapController(QObject):
    loading                  = pyqtSignal(bool)
    error                    = pyqtSignal(str)
    create_error             = pyqtSignal(str)
    join_error               = pyqtSignal(str)
    maps_loaded              = pyqtSignal(list)
    map_created              = pyqtSignal(dict)
    map_joined               = pyqtSignal(dict)
    map_removed              = pyqtSignal(str)   # map_id
    map_member_count_changed = pyqtSignal(str, int)   # map_id, new_count
    map_role_changed         = pyqtSignal(str, str)   # map_id, new_role
    map_presence_changed     = pyqtSignal(str, list)  # map_id, online_users
    map_tile_changed         = pyqtSignal(str, int, int, dict)  # map_id, q, r, payload
    map_road_added           = pyqtSignal(str, str, list, str)  # map_id, segment_id, waypoints, color
    map_road_removed         = pyqtSignal(str, str)             # map_id, road_id
    map_inner_edges_changed  = pyqtSignal(str, list)            # map_id, cells
    map_state_loaded         = pyqtSignal(dict)
    map_editor_error         = pyqtSignal(str)
    cell_details_loaded      = pyqtSignal(int, int, dict)   # q, r, payload
    cell_details_error       = pyqtSignal(int, int, str)    # q, r, message
    session_error            = pyqtSignal()           # invalid/expired session

    def __init__(self, transport_worker: TransportWorker, session: Session) -> None:
        super().__init__()
        self._worker  = transport_worker
        self._session = session
        self._pending: set[str] = set()
        self._details_pending: dict[str, tuple[int, int]] = {}
        self._open_map_id: str | None = None
        self._tile_ids: dict[tuple[int, int], str] = {}
        self._map_role: str = "viewer"
        transport_worker.response.connect(self._on_response)
        transport_worker.event.connect(self._on_event)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def get_maps(self) -> None:
        self._send(request("get_maps", {"token": self._session.token}))

    def create_map(self, name: str) -> None:
        name = name.strip()
        if not name:
            self.create_error.emit(_ERROR_MESSAGES["missing_fields"])
            return
        if len(name) > MAX_MAP_NAME_LEN:
            self.create_error.emit(_ERROR_MESSAGES["map_name_too_long"])
            return
        self._send(request("create_map", {"token": self._session.token, "name": name}))

    def join_map(self, code: str) -> None:
        self._send(request("join_map", {"token": self._session.token, "code": code}))

    def dissociate_map(self, map_id: str) -> None:
        self._send(request("dissociate_map", {"token": self._session.token, "map_id": map_id}))

    def delete_map(self, map_id: str) -> None:
        self._send(request("delete_map", {"token": self._session.token, "map_id": map_id}))

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

    def tile_id_at(self, q: int, r: int) -> str | None:
        return self._tile_ids.get((q, r))

    def remember_tile(self, q: int, r: int, tile_id: str) -> None:
        self._tile_ids[(q, r)] = tile_id

    def fetch_cell_details(self, q: int, r: int) -> None:
        """Lazy-load structure/description metadata for the inspector."""
        if not self._open_map_id:
            self.cell_details_error.emit(q, r, "No map is open.")
            return
        tile_id = self._tile_ids.get((q, r))
        if not tile_id:
            self.cell_details_loaded.emit(q, r, {})
            return
        req = request(
            "get_cell_details",
            {
                "token": self._session.token,
                "map_id": self._open_map_id,
                "tile_id": tile_id,
            },
        )
        self._details_pending[req["request_id"]] = (q, r)
        if not self._worker.submit(req):
            self._details_pending.pop(req["request_id"], None)
            self.cell_details_error.emit(q, r, _ERROR_MESSAGES["unexpected_error"])

    def set_structure(self, q: int, r: int, structure_type: str) -> None:
        if not self._open_map_id or not structure_type:
            return
        self._send(
            request(
                "set_structure",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "q": q,
                    "r": r,
                    "type": structure_type,
                },
            ),
        )

    def add_road(self, waypoints: list, color: str) -> None:
        """RF13: send a road polyline (>= 2 waypoints as [[q,r],...])."""
        if not self._open_map_id or not color or len(waypoints) < 2:
            return
        self._send(
            request(
                "add_road",
                {
                    "token": self._session.token,
                    "map_id": self._open_map_id,
                    "waypoints": waypoints,
                    "color": color,
                },
            ),
        )

    def remove_structure(self, q: int, r: int) -> None:
        tile_id = self._tile_ids.get((q, r))
        if not self._open_map_id or not tile_id:
            return
        self._send(
            request(
                "remove_structure",
                {"token": self._session.token, "map_id": self._open_map_id, "tile_id": tile_id},
            ),
        )

    def remove_road(self, road_id: str) -> None:
        if not self._open_map_id or not road_id:
            return
        self._send(
            request(
                "remove_road",
                {"token": self._session.token, "map_id": self._open_map_id, "road_id": road_id},
            ),
        )

    def set_inner_edge(self, q: int, r: int, edge_index: int, color: str) -> None:
        if not self._open_map_id or not color:
            return
        self._send(
            request(
                "set_inner_edge",
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

    def remove_inner_edge(self, q: int, r: int, edge_index: int) -> None:
        if not self._open_map_id:
            return
        self._send(
            request(
                "remove_inner_edge",
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
                {"token": self._session.token, "map_id": self._open_map_id, "tile_id": tile_id},
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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send(self, req: dict) -> None:
        self._pending.add(req["request_id"])
        if len(self._pending) == 1:
            self.loading.emit(True)
        if not self._worker.submit(req):
            self._pending.discard(req["request_id"])
            if not self._pending:
                self.loading.emit(False)
            self.error.emit(_ERROR_MESSAGES["unexpected_error"])

    def _on_response(self, response: dict) -> None:
        request_id = response.get("request_id", "")

        if request_id in self._details_pending:
            q, r = self._details_pending.pop(request_id)
            if response.get("status") == "error":
                code = response.get("code", "")
                if code == "invalid_token":
                    self.session_error.emit()
                    return
                msg = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
                self.cell_details_error.emit(q, r, msg)
            else:
                self.cell_details_loaded.emit(q, r, response.get("data", {}))
            return

        if request_id not in self._pending:
            return
        self._pending.discard(request_id)
        if not self._pending:
            self.loading.emit(False)

        req_type = response.get("type", "")

        if response.get("status") == "error":
            code = response.get("code", "")
            if code == "invalid_token":
                self.session_error.emit()
                return
            msg = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
            if req_type == "create_map":
                self.create_error.emit(msg)
            elif req_type == "join_map":
                self.join_error.emit(msg)
            elif req_type in (
                "get_map_state", "set_structure", "set_description",
                "add_road", "set_inner_edge", "remove_inner_edge",
                "remove_structure", "remove_road", "remove_description",
            ):
                self.map_editor_error.emit(msg)
            elif req_type == "close_map":
                pass
            else:
                self.error.emit(msg)
            return

        data = response.get("data", {})
        match req_type:
            case "get_maps":
                self.maps_loaded.emit(data.get("maps", []))
            case "get_map_state":
                self._map_role = data.get("role", "viewer")
                self.map_state_loaded.emit(data)
            case "set_structure" | "set_description":
                tile_id = data.get("tile_id")
                q, r = data.get("q"), data.get("r")
                if (
                    self._open_map_id
                    and tile_id is not None
                    and q is not None
                    and r is not None
                ):
                    self.remember_tile(int(q), int(r), tile_id)
            case "add_road":
                self._emit_road_segments(data)
            case "remove_structure" | "remove_road" | "remove_description":
                pass  # broadcast event drives the visual update
            case "set_inner_edge" | "remove_inner_edge":
                cells = data.get("cells", [])
                if self._open_map_id and cells:
                    self.map_inner_edges_changed.emit(self._open_map_id, cells)
            case "create_map":
                self.map_created.emit(data["map"])
            case "join_map":
                self.map_joined.emit(data["map"])
            case "dissociate_map" | "delete_map":
                self.map_removed.emit(data["map_id"])
            case "close_map":
                pass

    def _on_event(self, evt: dict) -> None:
        evt_type = evt.get("type", "")
        map_id   = evt.get("map_id", "")
        data     = evt.get("data", {})

        if evt_type in ("map_member_joined", "map_member_left"):
            self.map_member_count_changed.emit(map_id, data.get("member_count", 0))
        elif evt_type in ("map_user_online", "map_user_offline"):
            self.map_presence_changed.emit(map_id, data.get("online_users", []))
        elif evt_type == "map_ownership_transferred":
            if data.get("new_owner_id") == self._session.user_id:
                self.map_role_changed.emit(map_id, "owner")
        elif evt_type in (
            "structure_set",
            "structure_removed",
            "description_set",
            "description_removed",
        ):
            q, r = data.get("q"), data.get("r")
            if q is not None and r is not None:
                self.map_tile_changed.emit(map_id, int(q), int(r), data)
        elif evt_type == "road_added":
            self._emit_road_segments(data, map_id=map_id)
        elif evt_type == "road_removed":
            self.map_road_removed.emit(map_id, data.get("road_id", ""))
        elif evt_type == "inner_edge_changed":
            self.map_inner_edges_changed.emit(map_id, data.get("cells", []))

    def _emit_road_segments(self, data: dict, *, map_id: str | None = None) -> None:
        target_map_id = map_id or self._open_map_id
        if not target_map_id:
            return
        segments = data.get("segments")
        if segments is None:
            segments = [data]
        for segment in segments:
            road_id = segment.get("road_id", "")
            waypoints = segment.get("waypoints", [])
            color = segment.get("color", "")
            if road_id and waypoints and color:
                self.map_road_added.emit(target_map_id, road_id, waypoints, color)
