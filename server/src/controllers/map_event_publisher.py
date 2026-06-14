from services.presence_service import PresenceService
from transport.broadcaster import Broadcaster
from transport.protocol import event

class MapEventPublisher:
    def __init__(self, broadcaster: Broadcaster, presence_service: PresenceService) -> None:
        self._broadcaster = broadcaster
        self._presence_service = presence_service

    def get_online_users(self, map_id: str) -> list[dict]:
        return self._presence_service.list_online_users(map_id)

    def presence_changed(self, map_id: str, event_type: str) -> None:
        self._broadcaster.broadcast(
            map_id,
            event(event_type, {"online_users": self._presence_service.list_online_users(map_id)}),
        )

    def tile_changed(self, map_id: str, event_type: str, tile_data: dict) -> None:
        self._broadcaster.broadcast(map_id, event(event_type, tile_data))

    def path_added(self, map_id: str, data: dict) -> None:
        self._broadcaster.broadcast(map_id, event("path_added", data))

    def path_removed(self, map_id: str, path_id: str) -> None:
        self._broadcaster.broadcast(map_id, event("path_removed", {"path_id": path_id}))

    def edge_changed(self, map_id: str, data: dict) -> None:
        self._broadcaster.broadcast(map_id, event("edge_changed", data))

    def member_joined(self, map_id: str, member_count: int) -> None:
        self._broadcaster.broadcast(map_id, event("map_member_joined", {"member_count": member_count}))

    def member_left(self, map_id: str, member_count: int) -> None:
        self._broadcaster.broadcast(map_id, event("map_member_left", {"member_count": member_count}))

    def ownership_transferred(self, map_id: str, new_owner_id: str) -> None:
        self._broadcaster.broadcast(
            map_id,
            event("map_ownership_transferred", {"new_owner_id": new_owner_id}),
        )
