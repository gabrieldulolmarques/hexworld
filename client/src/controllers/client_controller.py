from PyQt6.QtCore import QTimer

from controllers.auth_controller import AuthController
from controllers.map_controller import MapController
from controllers.transport_worker import TransportWorker
from models.preferences import Preferences
from models.session import Session
from models.tile_format import map_state_for_view, tiles_from_server
from transport.client import Client
from views.auth_view import AuthView
from views.home_view import HomeView
from views.main_view import MainView
from views.map.constants import TOOL_DESCRIPTION, TOOL_ERASE, TOOL_STRUCTURE
from views.map_view import MapView

_RECONNECT_DELAY_MS = 5000


class ClientController:
    def __init__(self, main_view: MainView) -> None:
        self.main_view = main_view
        self.auth_view = AuthView()
        self.home_view = HomeView()
        self.map_view = MapView()

        main_view.stack.addWidget(self.auth_view)
        main_view.stack.addWidget(self.home_view)
        main_view.stack.addWidget(self.map_view)

        self.client = Client()
        self.transport_worker = TransportWorker(self.client)
        self.transport_worker.start()

        self.session = Session()
        self._stopping = False

        self.preferences = Preferences()
        self._restore_preferences()

        self.auth = AuthController(self.transport_worker, self.session, self.preferences)
        self.maps = MapController(self.transport_worker, self.session)
        self._connect_signals()

        if self.session.is_authenticated():
            self.auth.validate_session()

    def _connect_signals(self) -> None:
        # Auth
        self.auth_view.request_login.connect(self.auth.login)
        self.auth_view.request_register.connect(self.auth.register)
        self.home_view.request_logout.connect(self.auth.logout)
        self.auth.login_success.connect(self._show_home)
        self.auth.session_restored.connect(self._show_home)
        self.auth.register_success.connect(self._on_register_success)
        self.auth.logged_out.connect(self._show_auth)
        self.auth.session_error.connect(self._show_auth)
        self.auth.loading.connect(self._on_auth_loading)
        self.auth.error.connect(self._on_auth_error)

        # Maps — home
        self.home_view.request_create_map.connect(self.maps.create_map)
        self.home_view.request_join_map.connect(self.maps.join_map)
        self.home_view.request_dissociate_map.connect(self.maps.dissociate_map)
        self.home_view.request_delete_map.connect(self.maps.delete_map)
        self.home_view.request_open_map.connect(self._on_open_map)
        self.maps.maps_loaded.connect(self.home_view.set_maps)
        self.maps.map_created.connect(self._on_map_created)
        self.maps.map_joined.connect(self._on_map_joined)
        self.maps.map_removed.connect(self.home_view.remove_map)
        self.maps.create_error.connect(self.home_view.show_create_error)
        self.maps.join_error.connect(self.home_view.show_join_error)
        self.maps.error.connect(lambda msg: self.home_view.show_message(msg, level="error"))
        self.maps.session_error.connect(self._show_auth)
        self.maps.loading.connect(self._on_map_loading)
        self.maps.map_member_count_changed.connect(self.home_view.update_map_member_count)
        self.maps.map_member_count_changed.connect(self._on_map_member_count_changed)
        self.maps.map_role_changed.connect(self.home_view.update_map_role)

        # Maps — editor
        self.map_view.request_back.connect(self._on_map_back)
        self.maps.map_state_loaded.connect(self._on_map_state_loaded)
        self.maps.map_presence_changed.connect(self._on_map_presence_changed)
        self.maps.map_tile_changed.connect(self._on_map_tile_changed)
        self.maps.map_editor_error.connect(
            lambda msg: self.home_view.show_message(msg, level="error"),
        )
        self.map_view.hex_paint_clicked.connect(self._on_hex_paint_clicked)
        self.map_view.description_submitted.connect(self.maps.set_description)

        self.transport_worker.finished.connect(self._on_worker_finished)

    # ------------------------------------------------------------------
    # Auth callbacks
    # ------------------------------------------------------------------

    def _on_auth_loading(self, loading: bool) -> None:
        if self.main_view.stack.currentWidget() is self.home_view:
            self.home_view.set_loading(loading)
        else:
            self.auth_view.set_loading(loading)

    def _on_auth_error(self, message: str) -> None:
        if self.main_view.stack.currentWidget() is self.home_view:
            self.home_view.show_message(message, level="error")
        else:
            self.auth_view.show_message(message, level="error")

    def _on_register_success(self) -> None:
        self.auth_view.show_register_success()

    def _show_home(self, username: str) -> None:
        self.home_view.set_user(username)
        self.home_view.go_home()
        self.main_view.stack.setCurrentWidget(self.home_view)
        self.maps.get_maps()

    def _show_auth(self) -> None:
        self._restore_preferences()
        self.auth_view.reset()
        self.main_view.stack.setCurrentWidget(self.auth_view)

    def _restore_preferences(self) -> None:
        username, remember = self.preferences.load()
        self.auth_view.set_login_defaults(username, remember)

    # ------------------------------------------------------------------
    # Map callbacks
    # ------------------------------------------------------------------

    def _on_map_loading(self, loading: bool) -> None:
        self.home_view.set_create_loading(loading)
        self.home_view.set_join_loading(loading)

    def _on_map_created(self, data: dict) -> None:
        self.home_view.add_map(data)
        self.home_view.go_home()

    def _on_map_joined(self, data: dict) -> None:
        self.home_view.add_map(data)
        self.home_view.go_home()

    def _on_open_map(self, map_id: str) -> None:
        self.main_view.stack.setCurrentWidget(self.map_view)
        self.maps.open_map(map_id)

    def _on_map_back(self) -> None:
        self.maps.close_map()
        self.home_view.go_home()
        self.main_view.stack.setCurrentWidget(self.home_view)

    def _on_map_state_loaded(self, state: dict) -> None:
        canvas_tiles, tile_ids = tiles_from_server(state.get("tiles", []))
        for (q, r), tile_id in tile_ids.items():
            self.maps.remember_tile(q, r, tile_id)
        view_data = map_state_for_view(state)
        self.map_view.set_map(view_data)
        self.map_view.set_tiles(canvas_tiles)
        self.map_view.set_online_users(state.get("online_users", []))
        self.map_view.update_member_count(view_data.get("member_count", 0))

    def _on_map_member_count_changed(self, map_id: str, count: int) -> None:
        if map_id == self.maps.open_map_id:
            self.map_view.update_member_count(count)

    def _on_map_presence_changed(self, map_id: str, online_users: list) -> None:
        if map_id != self.maps.open_map_id:
            return
        self.map_view.set_online_users(online_users)

    def _on_map_tile_changed(
        self, map_id: str, q: int, r: int, payload: dict,
    ) -> None:
        if map_id != self.maps.open_map_id:
            return
        tile_id = payload.get("tile_id")
        if tile_id:
            self.maps.remember_tile(q, r, tile_id)
        self.map_view.apply_server_tile(q, r, payload)

    def _on_hex_paint_clicked(self, q: int, r: int) -> None:
        if not self.maps.can_edit:
            return
        tool = self.map_view.active_tool()
        if tool == TOOL_STRUCTURE:
            structure = self.map_view.selected_structure()
            if not structure:
                self.home_view.show_message(
                    "Select a structure from the palette first.",
                    level="error",
                )
                return
            self.maps.set_structure(q, r, structure)
        elif tool == TOOL_DESCRIPTION:
            self.map_view.prompt_description(q, r)
        elif tool == TOOL_ERASE:
            component = self.map_view.canvas.hovered_erase_component()
            if component == "structure":
                self.maps.remove_structure(q, r)
            elif component == "road":
                road_id = self.map_view.canvas.road_id_at(q, r)
                if road_id:
                    self.maps.remove_road(q, r, road_id)
            elif component == "description":
                self.maps.remove_description(q, r)

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _on_worker_finished(self) -> None:
        if self._stopping:
            return
        QTimer.singleShot(_RECONNECT_DELAY_MS, self._restart_worker)

    def _restart_worker(self) -> None:
        if self._stopping:
            return
        self.transport_worker.reset()
        self.transport_worker.start()

    def stop(self) -> None:
        self._stopping = True
        self.transport_worker.stop()
        self.client.stop()
