import Pyro5.api

@Pyro5.api.expose
class MapListener:
    """Remote object the client exposes so the server can push typed events.
    Each method just re-emits a Qt signal on the worker (queued to the UI thread)."""

    def __init__(self, worker) -> None:
        self._worker = worker

    @Pyro5.api.oneway
    def on_tile_changed(self, map_id: str, tile: dict) -> None:
        self._worker.evt_tile_changed.emit(
            map_id, int(tile.get("q")), int(tile.get("r")), tile
        )

    @Pyro5.api.oneway
    def on_path_added(self, map_id: str, path: dict) -> None:
        self._worker.evt_path_added.emit(map_id, path)

    @Pyro5.api.oneway
    def on_path_removed(self, map_id: str, path_id: str) -> None:
        self._worker.evt_path_removed.emit(map_id, path_id)

    @Pyro5.api.oneway
    def on_edge_changed(self, map_id: str, tiles: list) -> None:
        self._worker.evt_edge_changed.emit(map_id, tiles)

    @Pyro5.api.oneway
    def on_presence_changed(self, map_id: str, online_users: list) -> None:
        self._worker.evt_presence_changed.emit(map_id, online_users)

    @Pyro5.api.oneway
    def on_member_changed(self, map_id: str, member_count: int) -> None:
        self._worker.evt_member_changed.emit(map_id, int(member_count))

    @Pyro5.api.oneway
    def on_ownership_transferred(self, map_id: str, new_owner_id: str) -> None:
        self._worker.evt_ownership_transferred.emit(map_id, new_owner_id)
