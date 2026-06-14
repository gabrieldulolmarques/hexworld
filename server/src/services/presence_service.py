from repositories.user_map_repository import UserMapRepository
from transport.presence_registry import PresenceRegistry

class PresenceService:
    def __init__(
        self, presence_registry: PresenceRegistry, user_map_repository: UserMapRepository
    ) -> None:
        self._presence_registry = presence_registry
        self._user_map_repository = user_map_repository

    def list_online_users(self, map_id: str) -> list[dict]:
        seen: set[str] = set()
        users: list[dict] = []
        for connection in self._presence_registry.connections_for(map_id):
            user_id = connection.user_id
            if not user_id or user_id in seen:
                continue
            seen.add(user_id)
            role = self._user_map_repository.get_role(user_id, map_id) or "viewer"
            users.append({"username": connection.username or "unknown", "role": role})
        users.sort(key=lambda entry: entry["username"].lower())
        return users
