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
    map_state_loaded         = pyqtSignal(dict)
    map_editor_error         = pyqtSignal(str)
    session_error            = pyqtSignal()           # invalid/expired session

    def __init__(self, transport_worker: TransportWorker, session: Session) -> None:
        super().__init__()
        self._worker  = transport_worker
        self._session = session
        self._pending: set[str] = set()
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
            elif req_type in ("get_map_state", "set_structure"):
                self.map_editor_error.emit(msg)
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
            case "set_structure":
                tile_id = data.get("tile_id")
                q, r = data.get("q"), data.get("r")
                stype = data.get("type", "")
                if (
                    self._open_map_id
                    and tile_id is not None
                    and q is not None
                    and r is not None
                ):
                    qi, ri = int(q), int(r)
                    self.remember_tile(qi, ri, tile_id)
                    self.map_tile_changed.emit(
                        self._open_map_id,
                        qi,
                        ri,
                        {
                            "q": qi,
                            "r": ri,
                            "tile_id": tile_id,
                            "structure": {"type": stype},
                        },
                    )
            case "create_map":
                self.map_created.emit(data["map"])
            case "join_map":
                self.map_joined.emit(data["map"])
            case "dissociate_map" | "delete_map":
                self.map_removed.emit(data["map_id"])

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
            "road_added",
            "road_removed",
            "description_set",
            "description_removed",
        ):
            q, r = data.get("q"), data.get("r")
            if q is not None and r is not None:
                self.map_tile_changed.emit(map_id, int(q), int(r), data)
