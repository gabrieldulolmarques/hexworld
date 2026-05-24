"""Online presence for map editor sessions (RF09 / members bar)."""

from repositories.user_map_repository import get_role
from transport.broadcaster import broadcaster


def list_online_users(map_id: str) -> list[dict]:
    seen: set[str] = set()
    users: list[dict] = []
    for connection in broadcaster.connections_for(map_id):
        user_id = connection.user_id
        if (
            not user_id
            or user_id in seen
            or not connection.is_present_in(map_id)
        ):
            continue
        seen.add(user_id)
        role = get_role(user_id, map_id) or "viewer"
        users.append({"username": connection.username or "unknown", "role": role})
    users.sort(key=lambda entry: entry["username"].lower())
    return users


def broadcast_presence(map_id: str, event_type: str) -> None:
    from transport.protocol import event

    broadcaster.broadcast(
        map_id,
        event(event_type, {"online_users": list_online_users(map_id)}),
    )
