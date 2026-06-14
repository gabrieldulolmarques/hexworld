from threading import Lock

class PresenceRegistry:
    def __init__(self) -> None:
        self._map_connections: dict[str, set] = {}
        self._lock = Lock()

    def enter(self, map_id: str, connection) -> bool:
        with self._lock:
            connections = self._map_connections.setdefault(map_id, set())
            if connection in connections:
                return False
            connections.add(connection)
            return True

    def leave(self, map_id: str, connection) -> bool:
        with self._lock:
            connections = self._map_connections.get(map_id)
            if connections is None or connection not in connections:
                return False
            connections.discard(connection)
            if not connections:
                del self._map_connections[map_id]
            return True

    def leave_all(self, connection) -> list[str]:
        with self._lock:
            maps_left = [
                map_id
                for map_id, connections in list(self._map_connections.items())
                if connection in connections
            ]
            for map_id in maps_left:
                self._map_connections[map_id].discard(connection)
                if not self._map_connections[map_id]:
                    del self._map_connections[map_id]
            return maps_left

    def is_present(self, map_id: str, connection) -> bool:
        with self._lock:
            return connection in self._map_connections.get(map_id, set())

    def connections_for(self, map_id: str) -> list:
        with self._lock:
            return list(self._map_connections.get(map_id, ()))
