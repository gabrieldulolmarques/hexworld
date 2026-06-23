from threading import Lock

class RmiSessionRegistry:
    """Maps auth tokens to live Session objects (for resume and cleanup)."""

    def __init__(self) -> None:
        self._by_token: dict[str, object] = {}
        self._lock = Lock()

    def add(self, token: str, session: object) -> None:
        with self._lock:
            self._by_token[token] = session

    def get(self, token: str) -> object | None:
        with self._lock:
            return self._by_token.get(token)

    def remove(self, token: str) -> None:
        with self._lock:
            self._by_token.pop(token, None)

    def remove_session(self, session: object) -> None:
        with self._lock:
            tokens = [t for t, s in self._by_token.items() if s is session]
            for token in tokens:
                self._by_token.pop(token, None)
