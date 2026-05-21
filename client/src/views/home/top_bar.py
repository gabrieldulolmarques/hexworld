"""Top bar with Create / Join / user badge / Sign out controls."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

_BTN_WIDTH = 120
_BTN_HEIGHT = 46


class HomeTopBar(QWidget):
    create_clicked = pyqtSignal()
    join_clicked   = pyqtSignal()
    logout_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("homeTopBar")
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.user_badge = QLabel("")
        self.user_badge.setObjectName("userBadge")
        self.user_badge.hide()

        self.logout_button = QPushButton("Sign out")
        self.logout_button.setObjectName("danger")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.clicked.connect(self.logout_clicked)

        self.create_button = QPushButton("Create")
        self.create_button.setObjectName("primary")
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_button.clicked.connect(self.create_clicked)

        self.join_button = QPushButton("Join")
        self.join_button.setObjectName("secondary")
        self.join_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.join_button.clicked.connect(self.join_clicked)

        for btn in (self.create_button, self.join_button, self.logout_button):
            btn.setFixedSize(_BTN_WIDTH, _BTN_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)
        layout.addWidget(self.create_button)
        layout.addWidget(self.join_button)
        layout.addStretch(1)
        layout.addWidget(self.user_badge)
        layout.addWidget(self.logout_button)

    def set_user(self, username: str) -> None:
        self.user_badge.setText(f"⬢  {username}")
        self.user_badge.show()

    def set_logout_enabled(self, enabled: bool) -> None:
        self.logout_button.setEnabled(enabled)
