from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from views.map_card import CARD_WIDTH, MapCard
from views.widgets import HexLogo, StatusMixin, apply_panel_style, make_card_shadow

_PAGE_HOME   = 0
_PAGE_CREATE = 1
_PAGE_JOIN   = 2
_PAGE_SHARE  = 3

_TOP_BAR_BTN_WIDTH = 120
_TOP_BAR_BTN_HEIGHT = 46
_GRID_COLS = 3
_GRID_GAP = 14
_GRID_MARGIN_H = 64


class HomeView(StatusMixin, QWidget):
    request_logout        = pyqtSignal()
    request_create_map    = pyqtSignal(str)   # name
    request_join_map      = pyqtSignal(str)   # invite_code
    request_open_map      = pyqtSignal(str)   # map_id
    request_dissociate_map = pyqtSignal(str)  # map_id
    request_delete_map    = pyqtSignal(str)   # map_id

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("root")
        self._setup_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self._top_bar = self._build_top_bar()
        self._body    = QStackedWidget()
        self._body.addWidget(self._build_home_page())    # 0
        self._body.addWidget(self._build_create_page())  # 1
        self._body.addWidget(self._build_join_page())    # 2
        self._body.addWidget(self._build_share_page())  # 3

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar)
        root.addWidget(self._body, 1)

    def _build_top_bar(self) -> QWidget:
        self.user_badge = QLabel("")
        self.user_badge.setObjectName("userBadge")
        self.user_badge.hide()

        self.logout_button = QPushButton("Sign out")
        self.logout_button.setObjectName("danger")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.clicked.connect(self.request_logout)

        self.create_map_button = QPushButton("Create")
        self.create_map_button.setObjectName("primary")
        self.create_map_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_map_button.clicked.connect(lambda: self._go(_PAGE_CREATE))

        self.join_map_button = QPushButton("Join")
        self.join_map_button.setObjectName("secondary")
        self.join_map_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.join_map_button.clicked.connect(lambda: self._go(_PAGE_JOIN))

        for btn in (
            self.create_map_button,
            self.join_map_button,
            self.logout_button,
        ):
            btn.setFixedSize(_TOP_BAR_BTN_WIDTH, _TOP_BAR_BTN_HEIGHT)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)
        layout.addWidget(self.create_map_button)
        layout.addWidget(self.join_map_button)
        layout.addStretch(1)
        layout.addWidget(self.user_badge)
        layout.addWidget(self.logout_button)

        bar = QWidget()
        bar.setObjectName("homeTopBar")
        bar.setLayout(layout)
        return bar

    def _build_home_page(self) -> QWidget:
        self._maps_data: list[dict] = []

        # Empty state (shown when no maps)
        self._empty_state = self._build_empty_state()

        # Map cards: block centered on screen, cards flow from top-left inside
        self._cards_rows = QVBoxLayout()
        self._cards_rows.setContentsMargins(32, 20, 32, 20)
        self._cards_rows.setSpacing(_GRID_GAP)
        self._cards_rows.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )

        grid_width = (
            _GRID_COLS * CARD_WIDTH
            + (_GRID_COLS - 1) * _GRID_GAP
            + _GRID_MARGIN_H
        )
        cards_container = QWidget()
        cards_container.setLayout(self._cards_rows)
        cards_container.setFixedWidth(grid_width)
        cards_container.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Maximum,
        )

        self._cards_wrap = QWidget()
        wrap_layout = QHBoxLayout(self._cards_wrap)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        wrap_layout.addStretch(1)
        wrap_layout.addWidget(cards_container)
        wrap_layout.addStretch(1)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("mapScroll")
        self._scroll.setWidget(self._cards_wrap)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.hide()

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self._set_status_level("info")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)
        layout.addWidget(self._empty_state, 1)
        layout.addWidget(self._scroll, 1)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        return page

    def _build_empty_state(self) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        apply_panel_style(card)
        card.setFixedWidth(440)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        card.setGraphicsEffect(make_card_shadow())

        logo = HexLogo(size=96)
        brand = QLabel("HexWorld")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Start building collaborative hex maps.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(44, 44, 44, 48)
        card_layout.setSpacing(0)
        card_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(28)
        card_layout.addWidget(brand)
        card_layout.addSpacing(12)
        card_layout.addWidget(subtitle)

        wrapper = QWidget()
        wlayout = QVBoxLayout(wrapper)
        wlayout.setContentsMargins(0, 0, 0, 0)
        wlayout.addStretch(1)
        wlayout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        wlayout.addStretch(1)
        return wrapper

    def _build_create_page(self) -> QWidget:
        card = self._make_card()

        logo = HexLogo(size=72)
        brand = QLabel("New Map")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Name your new hex map.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(brand)
        header.addWidget(subtitle)

        name_label = QLabel("Map name")
        name_label.setObjectName("fieldLabel")

        self.create_name_input = QLineEdit()
        self.create_name_input.setPlaceholderText("My hex world")
        self.create_name_input.returnPressed.connect(self._submit_create)

        self.create_status_label = QLabel("")
        self.create_status_label.setObjectName("status")
        self.create_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.create_status_label.setWordWrap(True)

        self.create_confirm_button = QPushButton("Create Map")
        self.create_confirm_button.setDefault(True)
        self.create_confirm_button.clicked.connect(self._submit_create)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(lambda: self._go(_PAGE_HOME))

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel)
        buttons.addWidget(self.create_confirm_button)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 28)
        card_layout.setSpacing(10)
        card_layout.addLayout(header)
        card_layout.addSpacing(16)
        card_layout.addWidget(name_label)
        card_layout.addWidget(self.create_name_input)
        card_layout.addSpacing(8)
        card_layout.addLayout(buttons)
        card_layout.addWidget(self.create_status_label)

        return self._centered(card)

    def _build_join_page(self) -> QWidget:
        card = self._make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Join Map")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Enter your invite code to join a map.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(brand)
        header.addWidget(subtitle)

        code_label = QLabel("Invite code")
        code_label.setObjectName("fieldLabel")

        self.join_code_input = QLineEdit()
        self.join_code_input.setPlaceholderText("xxxx-xxxx")
        self.join_code_input.returnPressed.connect(self._submit_join)

        self.join_status_label = QLabel("")
        self.join_status_label.setObjectName("status")
        self.join_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.join_status_label.setWordWrap(True)

        self.join_confirm_button = QPushButton("Join Map")
        self.join_confirm_button.setDefault(True)
        self.join_confirm_button.clicked.connect(self._submit_join)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(lambda: self._go(_PAGE_HOME))

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel)
        buttons.addWidget(self.join_confirm_button)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 28)
        card_layout.setSpacing(10)
        card_layout.addLayout(header)
        card_layout.addSpacing(16)
        card_layout.addWidget(code_label)
        card_layout.addWidget(self.join_code_input)
        card_layout.addSpacing(8)
        card_layout.addLayout(buttons)
        card_layout.addWidget(self.join_status_label)

        return self._centered(card)

    def _build_share_page(self) -> QWidget:
        card = self._make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Share Map")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.share_subtitle = QLabel("")
        self.share_subtitle.setObjectName("subtitle")
        self.share_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share_subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(brand)
        header.addWidget(self.share_subtitle)

        hint = QLabel("Invite others with these codes.")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        (
            self.share_editor_section,
            self.share_editor_input,
            self.share_editor_copy,
        ) = self._make_share_code_section("Editor invite")
        (
            self.share_viewer_section,
            self.share_viewer_input,
            self.share_viewer_copy,
        ) = self._make_share_code_section("Viewer invite")

        self.share_status_label = QLabel("")
        self.share_status_label.setObjectName("status")
        self.share_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share_status_label.setWordWrap(True)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(lambda: self._go(_PAGE_HOME))

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 28)
        card_layout.setSpacing(10)
        card_layout.addLayout(header)
        card_layout.addSpacing(8)
        card_layout.addWidget(hint)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.share_editor_section)
        card_layout.addWidget(self.share_viewer_section)
        card_layout.addWidget(self.share_status_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(cancel)

        self.share_editor_section.hide()
        self.share_viewer_section.hide()

        return self._centered(card)

    def _make_share_code_section(
        self,
        label_text: str,
    ) -> tuple[QWidget, QLineEdit, QPushButton]:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")

        code_input = QLineEdit()
        code_input.setReadOnly(True)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("ghost")
        copy_btn.setProperty("shareCopy", "true")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(
            lambda: self._copy_invite_code(code_input, copy_btn),
        )

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(code_input, 1)
        row.addWidget(copy_btn)

        layout.addWidget(label)
        layout.addLayout(row)
        return section, code_input, copy_btn

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_card(width: int = 360) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        apply_panel_style(card)
        card.setFixedWidth(width)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        card.setGraphicsEffect(make_card_shadow())
        return card

    @staticmethod
    def _centered(widget: QWidget) -> QWidget:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        return body

    def _go(self, page: int) -> None:
        self._body.setCurrentIndex(page)
        if page == _PAGE_CREATE:
            self.create_name_input.clear()
            self.create_status_label.setText("")
            self.create_name_input.setFocus()
        elif page == _PAGE_JOIN:
            self.join_code_input.clear()
            self.join_status_label.setText("")
            self.join_code_input.setFocus()

    def _open_share_page(self, map_id: str) -> None:
        data = self._map_by_id(map_id)
        if data is None:
            return
        self._populate_share_page(data)
        self._go(_PAGE_SHARE)

    def _populate_share_page(self, data: dict) -> None:
        self.share_subtitle.setText(data["name"])
        editor_code = data.get("editor_code")
        viewer_code = data.get("viewer_code")

        if editor_code:
            self.share_editor_input.setText(editor_code)
            self.share_editor_section.show()
        else:
            self.share_editor_section.hide()

        if viewer_code:
            self.share_viewer_input.setText(viewer_code)
            self.share_viewer_section.show()
        else:
            self.share_viewer_section.hide()

        if editor_code or viewer_code:
            self.share_status_label.setText("")
        else:
            self._set_form_status(
                self.share_status_label,
                "You do not have permission to view share codes for this map.",
                "info",
            )

    @staticmethod
    def _copy_invite_code(code_input: QLineEdit, button: QPushButton) -> None:
        code = code_input.text().strip()
        if not code:
            return
        QGuiApplication.clipboard().setText(code)
        previous = button.text()
        button.setText("Copied!")

        def restore() -> None:
            button.setText(previous)

        QTimer.singleShot(1500, restore)

    def _map_by_id(self, map_id: str) -> dict | None:
        for entry in self._maps_data:
            if entry["id"] == map_id:
                return entry
        return None

    def _connect_card(self, card: MapCard) -> None:
        card.open_clicked.connect(self.request_open_map)
        card.share_clicked.connect(self._open_share_page)
        card.dissociate_clicked.connect(self.request_dissociate_map)
        card.delete_clicked.connect(self.request_delete_map)

    def _rebuild_cards(self) -> None:
        while self._cards_rows.count():
            item = self._cards_rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._maps_data:
            self._scroll.hide()
            self._empty_state.show()
            return

        self._empty_state.hide()
        self._scroll.show()

        for start in range(0, len(self._maps_data), _GRID_COLS):
            chunk = self._maps_data[start : start + _GRID_COLS]
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(_GRID_GAP)
            for data in chunk:
                card = MapCard(data)
                self._connect_card(card)
                row_layout.addWidget(card)
            self._cards_rows.addWidget(
                row_widget,
                alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            )

        self._cards_rows.addStretch(1)

    # ------------------------------------------------------------------
    # Submit handlers
    # ------------------------------------------------------------------

    def _submit_create(self) -> None:
        name = self.create_name_input.text().strip()
        if not name:
            self._set_form_status(self.create_status_label, "Map name is required.", "error")
            return
        self.request_create_map.emit(name)

    def _submit_join(self) -> None:
        code = self.join_code_input.text().strip()
        if not code:
            self._set_form_status(self.join_status_label, "Invite code is required.", "error")
            return
        self.request_join_map.emit(code)

    @staticmethod
    def _set_form_status(label: QLabel, text: str, level: str) -> None:
        label.setText(text)
        label.setProperty("level", level)
        label.style().unpolish(label)
        label.style().polish(label)

    # ------------------------------------------------------------------
    # Public API (controller)
    # ------------------------------------------------------------------

    def set_user(self, username: str) -> None:
        self.user_badge.setText(f"⬢  {username}")
        self.user_badge.show()

    def go_home(self) -> None:
        self._go(_PAGE_HOME)

    def set_maps(self, maps: list[dict]) -> None:
        self._maps_data = list(maps)
        self._rebuild_cards()

    def add_map(self, data: dict) -> None:
        self._maps_data.insert(0, data)
        self._rebuild_cards()

    def remove_map(self, map_id: str) -> None:
        self._maps_data = [m for m in self._maps_data if m["id"] != map_id]
        self._rebuild_cards()

    def update_map_member_count(self, map_id: str, count: int) -> None:
        for m in self._maps_data:
            if m["id"] == map_id:
                m["member_count"] = count
                break
        self._rebuild_cards()

    def update_map_role(self, map_id: str, role: str) -> None:
        for m in self._maps_data:
            if m["id"] == map_id:
                m["role"] = role
                break
        self._rebuild_cards()

    def set_loading(self, loading: bool) -> None:
        self.logout_button.setEnabled(not loading)
        if loading:
            self.show_message("Signing out…", level="info")
        else:
            self.show_message("", level="info")

    def set_create_loading(self, loading: bool) -> None:
        self.create_confirm_button.setEnabled(not loading)
        self.create_name_input.setEnabled(not loading)
        if loading:
            self.create_status_label.setText("Creating map…")

    def set_join_loading(self, loading: bool) -> None:
        self.join_confirm_button.setEnabled(not loading)
        self.join_code_input.setEnabled(not loading)
        if loading:
            self.join_status_label.setText("Joining map…")

    def show_create_error(self, message: str) -> None:
        self._set_form_status(self.create_status_label, message, "error")
        self.set_create_loading(False)

    def show_join_error(self, message: str) -> None:
        self._set_form_status(self.join_status_label, message, "error")
        self.set_join_loading(False)
