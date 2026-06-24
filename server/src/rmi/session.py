import logging
from threading import Lock, Thread

import Pyro5.api

from rmi.context import RmiContext
from rmi.errors import HexworldError
from rmi.map_session import MapSession

logger = logging.getLogger(__name__)

@Pyro5.api.expose
class Session:
    """One authenticated client. Also acts as the Broadcaster/Presence subscriber,
    translating internal dict events into typed calls on the client's listener."""

    def __init__(
        self, context: RmiContext, token: str, user_id: str, username: str
    ) -> None:
        self._ctx = context
        self._token = token
        self._user_id = user_id
        self._username = username
        self._listener_uri: str | None = None
        self._listener_proxy: Pyro5.api.Proxy | None = None
        self._subscribed_maps: set[str] = set()
        self._map_sessions: dict[str, MapSession] = {}
        self._closed = False
        self._lock = Lock()
        self._send_lock = Lock()

    # ---- subscriber interface used server-side by Presence/Broadcaster ----

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    def subscribe(self, map_id: str) -> None:
        self._ctx.broadcaster.subscribe(map_id, self)
        with self._lock:
            self._subscribed_maps.add(map_id)

    def unsubscribe(self, map_id: str) -> None:
        self._ctx.broadcaster.unsubscribe(map_id, self)
        with self._lock:
            self._subscribed_maps.discard(map_id)

    def enter_presence(self, map_id: str) -> bool:
        return self._ctx.presence.enter(map_id, self)

    def leave_presence(self, map_id: str) -> bool:
        return self._ctx.presence.leave(map_id, self)

    def send(self, payload: dict) -> None:
        failed = False
        with self._send_lock:
            if self._closed or not self._listener_uri:
                return
            try:
                self._dispatch_event(self._bound_listener(), payload)
            except Exception:
                failed = True
        if failed:
            logger.warning(
                "Listener push failed; cleaning up session for user %r", self._username
            )
            Thread(target=self.cleanup, daemon=True).start()

    # ---- remote methods (exposed to the client) ----

    def identity(self) -> dict:
        return {
            "token": self._token,
            "user_id": self._user_id,
            "username": self._username,
        }

    def register_listener(self, listener) -> None:
        uri = str(getattr(listener, "_pyroUri", listener) or "").strip()
        with self._send_lock:
            self._listener_uri = uri or None
            self._listener_proxy = None

    def get_maps(self) -> list[dict]:
        maps = self._ctx.map_service.get_maps(self._user_id)
        for entry in maps:
            self.subscribe(entry["id"])
        return maps

    def create_map(self, name: str) -> dict:
        result = _unwrap(self._ctx.map_service.create_map(self._user_id, name))
        self.subscribe(result["id"])
        return result

    def join_map(self, code: str) -> dict:
        result = _unwrap(self._ctx.map_service.join_map(self._user_id, code))
        map_id = result["id"]
        self._ctx.publisher.member_joined(map_id, result["member_count"])
        self.subscribe(map_id)
        return result

    def dissociate_map(self, map_id: str) -> dict:
        error, result = self._ctx.map_service.dissociate_map(self._user_id, map_id)
        if error:
            raise HexworldError(error)
        was_present = self.leave_presence(map_id)
        self.unsubscribe(map_id)
        if was_present:
            self._ctx.publisher.presence_changed(map_id, "map_user_offline")
        self._ctx.publisher.member_left(map_id, result["member_count"])
        if result["new_owner_id"]:
            self._ctx.publisher.ownership_transferred(map_id, result["new_owner_id"])
        self._discard_map_session(map_id)
        return {"map_id": map_id}

    def delete_map(self, map_id: str) -> dict:
        error = self._ctx.map_service.delete_map(self._user_id, map_id)
        if error:
            raise HexworldError(error)
        self.leave_presence(map_id)
        self.unsubscribe(map_id)
        self._discard_map_session(map_id)
        return {"map_id": map_id}

    def open_map(self, map_id: str) -> MapSession:
        if self._ctx.auth_service.get_user_role(self._user_id, map_id) is None:
            raise HexworldError("not_member")
        with self._lock:
            existing = self._map_sessions.get(map_id)
        if existing is not None:
            return existing
        map_session = MapSession(
            self,
            map_id,
            self._ctx.map_service,
            self._ctx.tile_service,
            self._ctx.path_service,
            self._ctx.edge_service,
            self._ctx.publisher,
        )
        self._ctx.daemon.register(map_session)
        with self._lock:
            self._map_sessions[map_id] = map_session
        map_session._enter()
        return map_session

    def close_map(self, map_id: str) -> dict:
        if self.leave_presence(map_id):
            self._ctx.publisher.presence_changed(map_id, "map_user_offline")
        self._discard_map_session(map_id)
        return {"map_id": map_id}

    def logout(self) -> None:
        token = self._token
        self.cleanup()
        if token:
            self._ctx.auth_service.logout(token)

    # ---- teardown ----

    def cleanup(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            map_sessions = list(self._map_sessions.values())
            self._map_sessions.clear()
            subscribed = list(self._subscribed_maps)
            self._subscribed_maps.clear()
        presence_maps = self._ctx.presence.leave_all(self)
        for map_session in map_sessions:
            self._unregister(map_session)
        for map_id in subscribed:
            self._ctx.broadcaster.unsubscribe(map_id, self)
        for map_id in presence_maps:
            self._ctx.publisher.presence_changed(map_id, "map_user_offline")
        with self._send_lock:
            self._listener_uri = None
            self._listener_proxy = None
        self._ctx.registry.remove_session(self)
        self._unregister(self)

    def _discard_map_session(self, map_id: str) -> None:
        with self._lock:
            map_session = self._map_sessions.pop(map_id, None)
        if map_session is not None:
            self._unregister(map_session)

    def _unregister(self, remote_object: object) -> None:
        try:
            self._ctx.daemon.unregister(remote_object)
        except Exception:
            pass

    def _bound_listener(self) -> Pyro5.api.Proxy | None:
        if self._listener_proxy is None and self._listener_uri:
            self._listener_proxy = Pyro5.api.Proxy(self._listener_uri)
        if self._listener_proxy is not None:
            self._listener_proxy._pyroClaimOwnership()
        return self._listener_proxy

    def _dispatch_event(self, listener: Pyro5.api.Proxy | None, payload: dict) -> None:
        if listener is None:
            return
        event_type = payload.get("type")
        map_id = payload.get("map_id")
        data = payload.get("data", {})
        if event_type in ("map_user_online", "map_user_offline"):
            listener.on_presence_changed(map_id, data.get("online_users", []))
        elif event_type in (
            "terrain_set",
            "terrain_removed",
            "description_set",
            "description_removed",
        ):
            listener.on_tile_changed(map_id, data)
        elif event_type == "path_added":
            listener.on_path_added(map_id, data)
        elif event_type == "path_removed":
            listener.on_path_removed(map_id, data.get("path_id", ""))
        elif event_type == "edge_changed":
            listener.on_edge_changed(map_id, data.get("tiles", []))
        elif event_type in ("map_member_joined", "map_member_left"):
            listener.on_member_changed(map_id, data.get("member_count", 0))
        elif event_type == "map_ownership_transferred":
            listener.on_ownership_transferred(map_id, data.get("new_owner_id"))

def _unwrap(result: dict | str) -> dict:
    if isinstance(result, str):
        raise HexworldError(result)
    return result
