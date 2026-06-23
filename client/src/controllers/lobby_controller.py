from PyQt6.QtCore import QObject, pyqtSignal

from models.limits import MAX_MAP_MEMBERS, MAX_MAP_NAME_LENGTH
from models.session import Session
from transport.rmi.worker import RemoteWorker

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

    def __init__(self, worker: RemoteWorker, session: Session) -> None:
        super().__init__()
        self._worker = worker
        self._session = session
        self._inflight = 0
        worker.evt_member_changed.connect(self._on_member_changed)
        worker.evt_ownership_transferred.connect(self._on_ownership_transferred)

    def get_maps(self) -> None:
        self._track(self._worker.get_maps())(self._on_maps_loaded, self._on_error)

    def create_map(self, name: str) -> None:
        name = name.strip()
        if not name:
            self.create_error.emit(_ERROR_MESSAGES["missing_fields"])
            return
        if len(name) > MAX_MAP_NAME_LENGTH:
            self.create_error.emit(_ERROR_MESSAGES["map_name_too_long"])
            return
        self._track(self._worker.create_map(name))(
            lambda data: self.map_created.emit(data),
            lambda code: self.create_error.emit(_message(code)),
        )

    def join_map(self, code: str) -> None:
        self._track(self._worker.join_map(code))(
            lambda data: self.map_joined.emit(data),
            lambda error_code: self.join_error.emit(_message(error_code)),
        )

    def dissociate_map(self, map_id: str) -> None:
        self._track(self._worker.dissociate_map(map_id))(
            lambda _data: self.map_removed.emit(map_id), self._on_error
        )

    def delete_map(self, map_id: str) -> None:
        self._track(self._worker.delete_map(map_id))(
            lambda _data: self.map_removed.emit(map_id), self._on_error
        )

    def _track(self, call):
        self._inflight += 1
        if self._inflight == 1:
            self.loading.emit(True)

        def bind(on_success, on_failure):
            call.succeeded.connect(lambda result: self._finish(on_success, result))
            call.failed.connect(lambda code: self._finish(on_failure, code))

        return bind

    def _finish(self, handler, value) -> None:
        self._inflight = max(0, self._inflight - 1)
        if self._inflight == 0:
            self.loading.emit(False)
        handler(value)

    def _on_maps_loaded(self, maps: list) -> None:
        self.maps_loaded.emit(maps)

    def _on_error(self, code: str) -> None:
        if code == "invalid_token":
            self.session_error.emit()
            return
        self.error.emit(_message(code))

    def _on_member_changed(self, map_id: str, member_count: int) -> None:
        self.map_member_count_changed.emit(map_id, member_count)

    def _on_ownership_transferred(self, map_id: str, new_owner_id: str) -> None:
        if new_owner_id == self._session.user_id:
            self.map_role_changed.emit(map_id, "owner")

def _message(code: str) -> str:
    return _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unexpected_error"])
