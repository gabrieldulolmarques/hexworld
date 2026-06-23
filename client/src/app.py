from pathlib import Path

from controllers.auth_controller import AuthController
from controllers.lobby_controller import LobbyController
from models.map.edit_history import EditHistory
from controllers.map_session_controller import MapSessionController
from controllers.map_sync_controller import MapSyncController
from models.preferences import Preferences
from models.map.local_map_state import LocalMapState
from models.session import Session
from models.map.tile_format import (
    edges_from_server,
    map_state_for_view,
    paths_from_server,
    tiles_from_server,
)
from services.export import default_filename, normalize_path, save_image
from transport.rmi.worker import RemoteWorker
from views.auth_view import AuthView
from views.lobby.lobby_view import LobbyView
from views.shell.main_view import MainView
from models.map.tool_ids import TOOL_SELECT
from views.map.map_view import MapView

_CONNECT_MESSAGE = "Connecting to server…"
_RECONNECT_MESSAGE = "Reconnecting to server…"

class ClientApp:
    def __init__(self, main_view: MainView) -> None:
        self.main_view = main_view
        self.auth_view = AuthView()
        self.lobby_view = LobbyView()
        self.local_map_state = LocalMapState()
        self.map_view = MapView(self.local_map_state)

        main_view.stack.addWidget(self.auth_view)
        main_view.stack.addWidget(self.lobby_view)
        main_view.stack.addWidget(self.map_view)

        self.worker = RemoteWorker()
        main_view.show_connection_status(_CONNECT_MESSAGE)

        self.session = Session()
        self._stopping = False
        self.history = EditHistory()
        self._current_map_name = ""
        self._inspector_coord: tuple[int, int] | None = None

        self.preferences = Preferences()
        self._restore_preferences()

        self.auth = AuthController(
            self.worker, self.session, self.preferences
        )
        self.lobby = LobbyController(self.worker, self.session)
        self.map_sync = MapSyncController(self.worker, self.session)
        self.map_session = MapSessionController(
            self.map_sync,
            self.history,
            self.map_view,
            self.local_map_state,
        )
        self._connect_signals()

        self.worker.start()

    def _connect_signals(self) -> None:
        self.auth_view.login_requested.connect(self.auth.login)
        self.auth_view.register_requested.connect(self.auth.register)
        self.lobby_view.logout_requested.connect(self.auth.logout)
        self.auth.login_success.connect(self._show_lobby)
        self.auth.session_restored.connect(self._on_session_restored)
        self.auth.register_success.connect(self._on_register_success)
        self.auth.logged_out.connect(self._show_auth)
        self.auth.session_error.connect(self._show_auth)
        self.auth.loading.connect(self._on_auth_loading)
        self.auth.error.connect(self._on_auth_error)

        self.lobby_view.create_map_requested.connect(self.lobby.create_map)
        self.lobby_view.join_map_requested.connect(self.lobby.join_map)
        self.lobby_view.dissociate_map_requested.connect(self.lobby.dissociate_map)
        self.lobby_view.delete_map_requested.connect(self.lobby.delete_map)
        self.lobby_view.open_map_requested.connect(self._on_open_map)
        self.lobby.maps_loaded.connect(self.lobby_view.set_maps)
        self.lobby.map_created.connect(self._on_map_created)
        self.lobby.map_joined.connect(self._on_map_joined)
        self.lobby.map_removed.connect(self.lobby_view.remove_map)
        self.lobby.create_error.connect(self.lobby_view.show_create_error)
        self.lobby.join_error.connect(self.lobby_view.show_join_error)
        self.lobby.error.connect(self._on_maps_error)
        self.lobby.session_error.connect(self._show_auth)
        self.lobby.loading.connect(self._on_map_loading)
        self.lobby.map_member_count_changed.connect(
            self.lobby_view.update_map_member_count
        )
        self.lobby.map_member_count_changed.connect(
            self._on_map_member_count_changed
        )
        self.lobby.map_role_changed.connect(self.lobby_view.update_map_role)

        self.map_view.back_requested.connect(self._on_map_back)
        self.map_sync.map_state_loaded.connect(self._on_map_state_loaded)
        self.map_sync.map_presence_changed.connect(self._on_map_presence_changed)
        self.map_sync.map_tile_changed.connect(self._on_map_tile_changed)
        self.map_sync.map_path_added.connect(self.map_session.handle_map_path_added)
        self.map_sync.map_path_removed.connect(self.map_session.handle_map_path_removed)
        self.map_sync.map_edges_changed.connect(
            self.map_session.handle_map_edges_changed
        )
        self.map_sync.editor_error.connect(self.map_session.handle_editor_error)
        self.map_view.hex_paint_clicked.connect(self.map_session.handle_hex_paint)
        self.map_view.path_drawn.connect(self.map_session.handle_path_drawn)
        self.map_view.edge_painted.connect(self.map_session.handle_edge_painted)
        self.map_view.description_submitted.connect(
            self.map_session.handle_description_submitted
        )
        self.map_view.undo_requested.connect(self.map_session.undo)
        self.map_view.redo_requested.connect(self.map_session.redo)
        self.history.can_undo_changed.connect(self.map_view.set_undo_enabled)
        self.history.can_redo_changed.connect(self.map_view.set_redo_enabled)
        self.map_view.export_requested.connect(self._on_export_requested)
        self.map_view.export_submitted.connect(self._on_export_submitted)
        self.map_view.hex_selected.connect(self._on_hex_selected_for_inspector)
        self.map_sync.tile_details_loaded.connect(self._on_tile_details_loaded)
        self.map_sync.tile_details_error.connect(self._on_tile_details_error)

        self.worker.connected.connect(self._on_transport_connected)
        self.worker.disconnected.connect(self._on_transport_disconnected)

    def _on_auth_loading(self, loading: bool) -> None:
        if self.main_view.stack.currentWidget() is self.lobby_view:
            self.lobby_view.set_loading(loading)
        else:
            self.auth_view.set_loading(loading)

    def _on_auth_error(self, message: str) -> None:
        if self.main_view.stack.currentWidget() is self.lobby_view:
            self.lobby_view.show_message(message, level="error")
        else:
            self.auth_view.show_message(message, level="error")

    def _on_register_success(self) -> None:
        self.auth_view.show_register_success()

    def _show_lobby(self, username: str) -> None:
        self.lobby_view.set_user(username)
        self.lobby_view.go_home()
        self.main_view.stack.setCurrentWidget(self.lobby_view)
        self.lobby.get_maps()

    def _on_session_restored(self, username: str) -> None:
        current = self.main_view.stack.currentWidget()
        if current is self.auth_view:
            self._show_lobby(username)
            return
        self.lobby_view.set_user(username)
        self._resync_after_reconnect()

    def _show_auth(self) -> None:
        self._restore_preferences()
        self.auth_view.reset()
        self.main_view.stack.setCurrentWidget(self.auth_view)

    def _restore_preferences(self) -> None:
        username, remember = self.preferences.load()
        self.auth_view.set_login_defaults(username, remember)

    def _on_map_loading(self, loading: bool) -> None:
        self.lobby_view.set_create_loading(loading)
        self.lobby_view.set_join_loading(loading)

    def _on_maps_error(self, message: str) -> None:
        self.lobby_view.show_message(message, level="error")

    def _on_map_created(self, data: dict) -> None:
        self.lobby_view.add_map(data)
        self.lobby_view.go_home()

    def _on_map_joined(self, data: dict) -> None:
        self.lobby_view.add_map(data)
        self.lobby_view.go_home()

    def _on_open_map(self, map_id: str) -> None:
        self.main_view.stack.setCurrentWidget(self.map_view)
        self.map_sync.open_map(map_id)

    def _on_map_back(self) -> None:
        self._clear_history()
        self._current_map_name = ""
        self._inspector_coord = None
        self.map_sync.close_map()
        self.lobby_view.go_home()
        self.main_view.stack.setCurrentWidget(self.lobby_view)

    def _on_map_state_loaded(self, state: dict) -> None:
        self._clear_history()
        self._inspector_coord = None
        canvas_tiles, tile_ids = tiles_from_server(state.get("tiles", []))
        for (q, r), tile_id in tile_ids.items():
            self.map_sync.remember_tile(q, r, tile_id)
        view_data = map_state_for_view(state)
        self._current_map_name = view_data.get("name", "")
        paths = paths_from_server(state.get("paths", []))
        edges = edges_from_server(state.get("edges", []))
        self.map_view.apply_full_map_state(
            tiles=canvas_tiles,
            paths=paths,
            edges=edges,
            online_users=state.get("online_users", []),
            meta=view_data,
        )

    def _on_map_member_count_changed(self, map_id: str, count: int) -> None:
        if map_id == self.map_sync.open_map_id:
            self.map_view.update_member_count(count)

    def _on_map_presence_changed(self, map_id: str, online_users: list) -> None:
        if map_id != self.map_sync.open_map_id:
            return
        self.map_view.set_online_users(online_users)

    def _on_hex_selected_for_inspector(self, q: int, r: int) -> None:
        if self.map_sync.open_map_id is None:
            return
        self._inspector_coord = (q, r)
        self.map_session.set_inspector_coord((q, r))
        self.map_view.set_inspector_details_loading()
        self.map_sync.get_tile_details(q, r)

    def _on_tile_details_loaded(self, q: int, r: int, details: dict) -> None:
        if self._inspector_coord != (q, r):
            return
        self.map_view.set_inspector_server_details(details)

    def _on_tile_details_error(self, q: int, r: int, message: str) -> None:
        if self._inspector_coord != (q, r):
            return
        self.map_view.set_inspector_server_details(None, error=message)

    def _on_map_tile_changed(
        self,
        map_id: str,
        q: int,
        r: int,
        payload: dict,
    ) -> None:
        if map_id != self.map_sync.open_map_id:
            return
        tile_id = payload.get("tile_id")
        if tile_id:
            self.map_sync.remember_tile(q, r, tile_id)
        self.map_view.apply_server_tile(q, r, payload)
        if (
            self._inspector_coord == (q, r)
            and self.map_view.active_tool() == TOOL_SELECT
        ):
            self.map_view.refresh_inspector(q, r)
            self.map_sync.get_tile_details(q, r)

    def _clear_history(self) -> None:
        self.map_session.clear_state()

    def _on_export_requested(self) -> None:
        self.map_view.open_export_dialog(
            str(Path.home() / default_filename(self._current_map_name))
        )

    def _on_export_submitted(self, path: str) -> None:
        export_path = normalize_path(Path(path))
        self.map_view.set_export_busy(True)
        image = self.map_view.export_full_map_image()
        if save_image(image, export_path):
            self.map_view.show_export_success(str(export_path))
        else:
            self.map_view.show_export_error(
                "The full map image could not be generated or saved.",
            )

    def _on_transport_disconnected(self) -> None:
        if self._stopping:
            return
        self.auth.handle_transport_dropped()
        self.main_view.show_connection_status(_RECONNECT_MESSAGE)

    def _on_transport_connected(self) -> None:
        if self._stopping:
            return
        self.main_view.show_connection_status(None)
        if self.session.is_authenticated():
            self.auth.validate_session()

    def _resync_after_reconnect(self) -> None:
        current = self.main_view.stack.currentWidget()
        if current is self.map_view and self.map_sync.open_map_id:
            self.map_sync.open_map(self.map_sync.open_map_id)
        elif current is self.lobby_view:
            self.lobby.get_maps()

    def stop(self) -> None:
        self._stopping = True
        self.worker.stop()
