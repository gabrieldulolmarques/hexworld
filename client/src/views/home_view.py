from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.widgets import HexLogo, StatusMixin, horizontal_divider, make_card_shadow

class HomeView(StatusMixin, QWidget):
    request_logout = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("root")
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.user_badge = QLabel("")
        self.user_badge.setObjectName("userBadge")
        self.user_badge.hide()

        self.logout_button = QPushButton("Sign out")
        self.logout_button.setObjectName("ghost")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.clicked.connect(self.request_logout)

        top_bar_inner = QHBoxLayout()
        top_bar_inner.setContentsMargins(20, 12, 20, 12)
        top_bar_inner.setSpacing(10)
        top_bar_inner.addStretch(1)
        top_bar_inner.addWidget(self.user_badge)
        top_bar_inner.addWidget(self.logout_button)

        top_bar = QWidget()
        top_bar.setLayout(top_bar_inner)

        card = QWidget()
        card.setObjectName("card")
        card.setFixedWidth(440)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        card.setGraphicsEffect(make_card_shadow())

        card_logo = HexLogo(size=80)

        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setObjectName("welcome")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setWordWrap(True)

        tagline = QLabel(
            "You're signed in. Soon you'll be able to create maps, "
            "collaborate in real time, and edit the hex grid."
        )
        tagline.setObjectName("subtitle")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setWordWrap(True)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self._set_status_level("info")

        coming_soon_title = QLabel("Coming soon")
        coming_soon_title.setObjectName("fieldLabel")
        coming_soon_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        coming_soon = QLabel(
            "⬢  Create and share maps\n"
            "⬢  Real-time collaborative editing\n"
            "⬢  Structures, roads, and per-cell descriptions"
        )
        coming_soon.setObjectName("subtitle")
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 24, 36, 32)
        card_layout.setSpacing(12)
        card_layout.addWidget(card_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(14)
        card_layout.addWidget(self.welcome_label)
        card_layout.addWidget(tagline)
        card_layout.addWidget(self.status_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(horizontal_divider())
        card_layout.addSpacing(8)
        card_layout.addWidget(coming_soon_title)
        card_layout.addWidget(coming_soon)

        body = QVBoxLayout()
        body.setContentsMargins(16, 12, 16, 16)
        body.setSpacing(0)
        body.addStretch(1)
        body.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        body.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(top_bar)
        root.addLayout(body, 1)

    def set_user(self, user_id: str) -> None:
        short = user_id.split("-")[0] if "-" in user_id else user_id
        self.welcome_label.setText("Welcome back!")
        self.user_badge.setText(f"⬢  {short}")
        self.user_badge.show()

    def set_loading(self, loading: bool) -> None:
        self.logout_button.setEnabled(not loading)
        if loading:
            self.show_message("Signing out…", level="info")
        else:
            self.show_message("", level="info")
