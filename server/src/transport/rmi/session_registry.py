from threading import Lock

from transport.broadcaster import Broadcaster
from transport.presence import Presence
from transport.rmi.client_session import BroadcastPresenceFn, RmiClientSession

class RmiSessionRegistry:
    """Per-client RMI sessions keyed by auth token.

    The remote objects are stateless facades shared by every client, so the
    per-client state (subscriptions, presence, event callback) lives here and
    is resolved by the token carried on each authenticated call.
    """

    def __init__(
        self,
        broadcaster: Broadcaster,
        presence: Presence,
        broadcast_presence: BroadcastPresenceFn,
    ) -> None:
        self._broadcaster = broadcaster
        self._presence = presence
        self._broadcast_presence = broadcast_presence
        self._sessions: dict[str, RmiClientSession] = {}
        self._lock = Lock()

    def get_or_create(self, token: str) -> RmiClientSession:
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                session = self._new_session()
                self._sessions[token] = session
            return session

    def transient(self) -> RmiClientSession:
        """Untracked session for unauthenticated calls (register/login)."""
        return self._new_session()

    def remove(self, token: str) -> None:
        with self._lock:
            session = self._sessions.pop(token, None)
        if session is not None:
            session.cleanup()

    def _new_session(self) -> RmiClientSession:
        return RmiClientSession(
            self._broadcaster, self._presence, self._broadcast_presence
        )
