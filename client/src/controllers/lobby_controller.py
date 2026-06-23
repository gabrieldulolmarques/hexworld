from PyQt6.QtCore import QObject, pyqtSignal

from models.limits import MAX_MAP_MEMBERS, MAX_MAP_NAME_LENGTH
from models.session import Session
from transport.messages import STATUS_ERROR, request
from transport.rmi.proxy_worker import ProxyWorker

_ERROR_MESSAGES = {
    "missing_fields": "Missing fields.",
    "map_name_too_long": "Map name is too long.",
    "invalid_code": "Invalid invite code.",
    "already_member": "You are already a member of this map.",
    "map_full": f"This map is full ({MAX_MAP_MEMBERS} members max).",
    "not_member": "You are not a member of this map.",
    "not_owner": "Only the owner can delete this map.",
    "map_has_members": "Remove all other members before deleting.",
    "use_delete": "You are the only member — use Delete instead.",
    "unexpected_error": "Unexpected server error.",
}

class LobbyController(QObject):
    loading = pyqtSignal(bool)
    error = pyqtSignal(str)
    create_error = pyqtSignal(str)
    join_error = pyqtSignal(str)
    maps_loaded = pyqtSignal(list)
    map_created = pyqtSignal(dict)
    map_joined = pyqtSignal(dict)
    map_removed = pyqtSignal(str)
    map_member_count_changed = pyqtSignal(str, int)
    map_role_changed = pyqtSignal(str, str)
    session_error = pyqtSignal()

    def __init__(self, worker: ProxyWorker, session: Session) -> None:
        super().__init__()
        self._worker = worker
        self._session = session
        self._pending: set[str] = set()
        worker.response.connect(self._on_response)
        worker.event.connect(self._on_event)

    def get_maps(self) -> None:
        self._send(request("get_maps", {"token": self._session.token}))

    def create_map(self, name: str) -> None:
        name = name.strip()
        if not name:
            self.create_error.emit(_ERROR_MESSAGES["missing_fields"])
            return
        if len(name) > MAX_MAP_NAME_LENGTH:
            self.create_error.emit(_ERROR_MESSAGES["map_name_too_long"])
            return
        self._send(request("create_map", {"token": self._session.token, "name": name}))

    def join_map(self, code: str) -> None:
        self._send(request("join_map", {"token": self._session.token, "code": code}))

    def dissociate_map(self, map_id: str) -> None:
        self._send(
            request("dissociate_map", {"token": self._session.token, "map_id": map_id})
        )

    def delete_map(self, map_id: str) -> None:
        self._send(
            request("delete_map", {"token": self._session.token, "map_id": map_id})
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
            if req_type == "create_map":
                self.create_error.emit(message)
            elif req_type == "join_map":
                self.join_error.emit(message)
            else:
                self.error.emit(message)
            return

        data = response.get("data", {})
        match req_type:
            case "get_maps":
                self.maps_loaded.emit(data.get("maps", []))
            case "create_map":
                self.map_created.emit(data["map"])
            case "join_map":
                self.map_joined.emit(data["map"])
            case "dissociate_map" | "delete_map":
                self.map_removed.emit(data["map_id"])

    def _on_event(self, evt: dict) -> None:
        evt_type = evt.get("type", "")
        map_id = evt.get("map_id", "")
        data = evt.get("data", {})

        if evt_type in ("map_member_joined", "map_member_left"):
            self.map_member_count_changed.emit(map_id, data.get("member_count", 0))
        elif evt_type == "map_ownership_transferred":
            if data.get("new_owner_id") == self._session.user_id:
                self.map_role_changed.emit(map_id, "owner")
