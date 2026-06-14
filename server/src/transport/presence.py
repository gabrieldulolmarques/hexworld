from threading import Lock

from transport.session import ClientSession

class Presence:
    def __init__(self) -> None:
        self._map_connections: dict[str, set[ClientSession]] = {}
        self._lock = Lock()

    def enter(self, map_id: str, session: ClientSession) -> bool:
        with self._lock:
            connections = self._map_connections.setdefault(map_id, set())
            if session in connections:
                return False
            connections.add(session)
            return True

    def leave(self, map_id: str, session: ClientSession) -> bool:
        with self._lock:
            connections = self._map_connections.get(map_id)
            if connections is None or session not in connections:
                return False
            connections.discard(session)
            if not connections:
                del self._map_connections[map_id]
            return True

    def leave_all(self, session: ClientSession) -> list[str]:
        with self._lock:
            maps_left = [
                map_id
                for map_id, connections in list(self._map_connections.items())
                if session in connections
            ]
            for map_id in maps_left:
                self._map_connections[map_id].discard(session)
                if not self._map_connections[map_id]:
                    del self._map_connections[map_id]
            return maps_left

    def is_present(self, map_id: str, session: ClientSession) -> bool:
        with self._lock:
            return session in self._map_connections.get(map_id, set())

    def connections_for(self, map_id: str) -> list[ClientSession]:
        with self._lock:
            return list(self._map_connections.get(map_id, ()))
