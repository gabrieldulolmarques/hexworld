import logging
from collections.abc import Callable
from threading import Lock

import Pyro5.api

from transport.broadcaster import Broadcaster
from transport.presence import Presence

logger = logging.getLogger(__name__)

BroadcastPresenceFn = Callable[[str, str], None]

class RmiClientSession:
    def __init__(
        self,
        broadcaster: Broadcaster,
        presence: Presence,
        broadcast_presence: BroadcastPresenceFn,
    ) -> None:
        self._broadcaster = broadcaster
        self._presence = presence
        self._broadcast_presence = broadcast_presence
        self._send_lock = Lock()
        self._event_callback_uri: str | None = None
        self._subscribed_maps: set[str] = set()
        self._user_id: str | None = None
        self._username: str | None = None

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def username(self) -> str | None:
        return self._username

    def set_event_callback(self, callback_uri: str) -> None:
        self._event_callback_uri = callback_uri

    def bind_user(self, user_id: str, username: str) -> None:
        self._user_id = user_id
        self._username = username

    def send(self, payload: dict) -> None:
        with self._send_lock:
            if self._event_callback_uri is None:
                # Subscribed but no callback yet (or already torn down): drop this
                # event silently. Raising here would make the Broadcaster evict a
                # still-valid subscriber on a transient gap.
                logger.debug(
                    "RMI session has no event callback; dropping event %s",
                    payload.get("type"),
                )
                return
            # A fresh Proxy is created per send so it is owned by the broadcasting
            # thread (Pyro proxies are not shareable across threads). A real
            # delivery failure propagates so the Broadcaster can evict a dead
            # subscriber.
            callback = Pyro5.api.Proxy(self._event_callback_uri)
            try:
                callback.on_event(payload)
            except Exception:
                logger.exception("Error sending event to RMI callback")
                raise

    def subscribe(self, map_id: str) -> None:
        self._broadcaster.subscribe(map_id, self)
        self._subscribed_maps.add(map_id)

    def unsubscribe(self, map_id: str) -> None:
        self._broadcaster.unsubscribe(map_id, self)
        self._subscribed_maps.discard(map_id)

    def enter_presence(self, map_id: str) -> bool:
        return self._presence.enter(map_id, self)

    def leave_presence(self, map_id: str) -> bool:
        return self._presence.leave(map_id, self)

    def cleanup(self) -> None:
        presence_maps = self._presence.leave_all(self)
        for map_id in list(self._subscribed_maps):
            self._broadcaster.unsubscribe(map_id, self)
        self._subscribed_maps.clear()
        for map_id in presence_maps:
            self._broadcast_presence(map_id, "map_user_offline")
        self._event_callback_uri = None
