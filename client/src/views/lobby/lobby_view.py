from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from views.lobby.create_page import CreatePage
from views.lobby.join_page import JoinPage
from views.lobby.map_grid import MapGrid
from views.lobby.share_page import SharePage
from views.lobby.top_bar import TopBar

_PAGE_HOME = 0
_PAGE_CREATE = 1
_PAGE_JOIN = 2
_PAGE_SHARE = 3

class LobbyView(QWidget):
    logout_requested = pyqtSignal()
    create_map_requested = pyqtSignal(str)
    join_map_requested = pyqtSignal(str)
    open_map_requested = pyqtSignal(str)
    dissociate_map_requested = pyqtSignal(str)
    delete_map_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lobbyScreen")
        self._setup_ui()
        self._wire_signals()

    def _setup_ui(self) -> None:
        self._top_bar = TopBar()
        self._map_grid = MapGrid()
        self._create_page = CreatePage()
        self._join_page = JoinPage()
        self._share_page = SharePage()

        self._body = QStackedWidget()
        self._body.addWidget(self._map_grid)
        self._body.addWidget(self._create_page)
        self._body.addWidget(self._join_page)
        self._body.addWidget(self._share_page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar)
        root.addWidget(self._body, 1)

    def _wire_signals(self) -> None:
        self._top_bar.logout_clicked.connect(self.logout_requested)
        self._top_bar.create_clicked.connect(self._show_create_page)
        self._top_bar.join_clicked.connect(self._show_join_page)

        self._map_grid.open_clicked.connect(self.open_map_requested)
        self._map_grid.share_clicked.connect(self._open_share_page)
        self._map_grid.dissociate_clicked.connect(self.dissociate_map_requested)
        self._map_grid.delete_clicked.connect(self.delete_map_requested)

        self._create_page.create_submitted.connect(self.create_map_requested)
        self._create_page.cancelled.connect(self._show_map_grid)
        self._join_page.join_submitted.connect(self.join_map_requested)
        self._join_page.cancelled.connect(self._show_map_grid)
        self._share_page.cancelled.connect(self._show_map_grid)

    def set_user(self, username: str) -> None:
        self._top_bar.set_user(username)

    def go_home(self) -> None:
        self._go(_PAGE_HOME)

    def set_maps(self, maps: list[dict]) -> None:
        self._map_grid.set_maps(maps)

    def add_map(self, data: dict) -> None:
        self._map_grid.add_map(data)

    def remove_map(self, map_id: str) -> None:
        self._map_grid.remove_map(map_id)

    def update_map_member_count(self, map_id: str, count: int) -> None:
        self._map_grid.update_member_count(map_id, count)

    def update_map_role(self, map_id: str, role: str) -> None:
        self._map_grid.update_role(map_id, role)

    def set_loading(self, loading: bool) -> None:
        self._top_bar.set_logout_enabled(not loading)
        if loading:
            self._map_grid.show_message("Signing out…", level="info")
        else:
            self._map_grid.show_message("", level="info")

    def set_create_loading(self, loading: bool) -> None:
        self._create_page.set_loading(loading)

    def set_join_loading(self, loading: bool) -> None:
        self._join_page.set_loading(loading)

    def show_create_error(self, message: str) -> None:
        self._create_page.show_error(message)

    def show_join_error(self, message: str) -> None:
        self._join_page.show_error(message)

    def show_message(self, message: str, level: str = "info") -> None:
        self._map_grid.show_message(message, level)

    def _go(self, page: int) -> None:
        self._body.setCurrentIndex(page)
        if page == _PAGE_CREATE:
            self._create_page.focus()
        elif page == _PAGE_JOIN:
            self._join_page.focus()

    def _show_map_grid(self) -> None:
        self._go(_PAGE_HOME)

    def _show_create_page(self) -> None:
        self._go(_PAGE_CREATE)

    def _show_join_page(self) -> None:
        self._go(_PAGE_JOIN)

    def _open_share_page(self, map_id: str) -> None:
        data = self._map_grid.map_by_id(map_id)
        if data is None:
            return
        self._share_page.populate(data)
        self._go(_PAGE_SHARE)
