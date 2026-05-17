from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.widgets import HexLogo, StatusMixin, make_card_shadow

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

        self.welcome_label = QLabel("Welcome back!")
        self.welcome_label.setObjectName("welcome")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setWordWrap(True)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self._set_status_level("info")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 24, 36, 32)
        card_layout.setSpacing(12)
        card_layout.addWidget(card_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(14)
        card_layout.addWidget(self.welcome_label)
        card_layout.addWidget(self.status_label)

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

    def set_user(self, username: str) -> None:
        self.user_badge.setText(f"⬢  {username}")
        self.user_badge.show()

    def set_loading(self, loading: bool) -> None:
        self.logout_button.setEnabled(not loading)
        if loading:
            self.show_message("Signing out…", level="info")
        else:
            self.show_message("", level="info")
