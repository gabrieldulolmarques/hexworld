"""Top bar with Create / Join / user badge / Sign out controls."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from limits import MAX_USERNAME_LEN
from styles.ui_constants import BTN_DANGER, BTN_PRIMARY, BTN_SECONDARY
from views.layout_utils import relayout_after_content_change
from views.ui_buttons import make_toolbar_button

_BADGE_MAX_PX = 160   # badge should not push the buttons off screen


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

        self.create_button = make_toolbar_button("Create", variant=BTN_PRIMARY)
        self.create_button.clicked.connect(self.create_clicked)

        self.join_button = make_toolbar_button("Join", variant=BTN_SECONDARY)
        self.join_button.clicked.connect(self.join_clicked)

        self.logout_button = make_toolbar_button("Sign out", variant=BTN_DANGER)
        self.logout_button.clicked.connect(self.logout_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)
        layout.addWidget(self.create_button)
        layout.addWidget(self.join_button)
        layout.addStretch(1)
        layout.addWidget(self.user_badge)
        layout.addWidget(self.logout_button)

    def set_user(self, username: str) -> None:
        metrics = QFontMetrics(self.user_badge.font())
        elided = metrics.elidedText(username, Qt.TextElideMode.ElideRight, _BADGE_MAX_PX)
        self.user_badge.setText(f"⬢  {elided}")
        self.user_badge.setToolTip(username if elided != username else "")
        self.user_badge.show()
        relayout_after_content_change(self)

    def set_logout_enabled(self, enabled: bool) -> None:
        self.logout_button.setEnabled(enabled)
