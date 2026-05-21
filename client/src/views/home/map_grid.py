"""Maps grid + empty state + status label.

The empty state shows the HexWorld logo card while the grid view appears
once the user has at least one map.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.map_card import CARD_WIDTH, MapCard
from views.widgets import (
    HexLogo,
    StatusMixin,
    apply_panel_style,
    make_card_shadow,
)

_GRID_COLS = 3
_GRID_GAP = 14
_GRID_MARGIN_H = 64


class MapGrid(StatusMixin, QWidget):
    """Scrollable grid of MapCards; falls back to a friendly empty state."""

    open_clicked       = pyqtSignal(str)
    share_clicked      = pyqtSignal(str)
    dissociate_clicked = pyqtSignal(str)
    delete_clicked     = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._maps_data: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._empty_state = self._build_empty_state()

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)
        layout.addWidget(self._empty_state, 1)
        layout.addWidget(self._scroll, 1)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    @staticmethod
    def _build_empty_state() -> QWidget:
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def maps(self) -> list[dict]:
        return self._maps_data

    def map_by_id(self, map_id: str) -> dict | None:
        for entry in self._maps_data:
            if entry["id"] == map_id:
                return entry
        return None

    def set_maps(self, maps: list[dict]) -> None:
        self._maps_data = list(maps)
        self._rebuild_cards()

    def add_map(self, data: dict) -> None:
        self._maps_data.insert(0, data)
        self._rebuild_cards()

    def remove_map(self, map_id: str) -> None:
        self._maps_data = [m for m in self._maps_data if m["id"] != map_id]
        self._rebuild_cards()

    def update_member_count(self, map_id: str, count: int) -> None:
        for m in self._maps_data:
            if m["id"] == map_id:
                m["member_count"] = count
                break
        self._rebuild_cards()

    def update_role(self, map_id: str, role: str) -> None:
        for m in self._maps_data:
            if m["id"] == map_id:
                m["role"] = role
                break
        self._rebuild_cards()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _connect_card(self, card: MapCard) -> None:
        card.open_clicked.connect(self.open_clicked)
        card.share_clicked.connect(self.share_clicked)
        card.dissociate_clicked.connect(self.dissociate_clicked)
        card.delete_clicked.connect(self.delete_clicked)

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
