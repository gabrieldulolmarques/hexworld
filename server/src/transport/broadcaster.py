from collections import defaultdict
from threading import Lock
from traceback import format_exc

class Broadcaster:
    """Per-map fanout for server-pushed events.

    Subscribers are `Connection` objects (any duck-typed `.send(payload)` works).
    Each broadcast stamps a monotonic `seq` per map_id so clients can detect
    gaps and request resend (spec §2.9 / RF17).
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, set] = defaultdict(set)
        self._sequences: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def subscribe(self, map_id: str, connection) -> None:
        with self._lock:
            self._subscribers[map_id].add(connection)

    def connections_for(self, map_id: str) -> list:
        with self._lock:
            return list(self._subscribers.get(map_id, ()))

    def unsubscribe(self, map_id: str, connection) -> None:
        with self._lock:
            subscribers = self._subscribers.get(map_id)
            if subscribers is None:
                return
            subscribers.discard(connection)
            if not subscribers:
                del self._subscribers[map_id]

    def broadcast(self, map_id: str, event: dict) -> None:
        with self._lock:
            self._sequences[map_id] += 1
            seq = self._sequences[map_id]
            recipients = list(self._subscribers.get(map_id, ()))
        stamped = {**event, "seq": seq, "map_id": map_id}
        failed = []
        for connection in recipients:
            try:
                connection.send(stamped)
            except Exception as exception:
                print(f"Error broadcasting event for map {map_id}: {exception}")
                print(format_exc())
                failed.append(connection)
        if failed:
            with self._lock:
                for connection in failed:
                    self._subscribers[map_id].discard(connection)
                if not self._subscribers.get(map_id):
                    self._subscribers.pop(map_id, None)

broadcaster = Broadcaster()
