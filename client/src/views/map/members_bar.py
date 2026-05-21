"""Bottom-left card — collapsible online-members list and Close Map button."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from styles.ui_constants import BTN_ACCENT, LABEL_CLOSE_MAP
from views.map.icons import tinted_pixmap
from views.map.panel import MapPanel
from views.ui_buttons import make_toolbar_button
from views.widgets import horizontal_divider


def _make_user_row(username: str, role: str) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    bullet = QLabel("●")
    bullet.setObjectName("mapRole")
    bullet.setProperty("role", role)

    name_lbl = QLabel(username)
    name_lbl.setObjectName("onlinePanelUser")

    role_lbl = QLabel(f"[{role.capitalize()}]")
    role_lbl.setObjectName("mapRole")
    role_lbl.setProperty("role", role)

    layout.addWidget(bullet)
    layout.addWidget(name_lbl)
    layout.addWidget(role_lbl)
    layout.addStretch(1)
    return row


class MembersBar(MapPanel):
    toggled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("mapBottomBar")
        self._expanded = False
        self._rows: list[QWidget] = []
        self._online = 0
        self._total = 0

        users_icon = QLabel()
        users_icon.setPixmap(tinted_pixmap("users.svg", "#9f9fa9", 18))

        self._count_lbl = QLabel("Members")
        self._count_lbl.setObjectName("onlinePanelTitle")

        self._expand_btn = QPushButton()
        self._expand_btn.setObjectName("onlinePanelCollapse")
        self._expand_btn.setIcon(QIcon(tinted_pixmap("chevron-up.svg", "#9f9fa9", 16)))
        self._expand_btn.setIconSize(QSize(16, 16))
        self._expand_btn.setFixedSize(28, 28)
        self._expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_btn.clicked.connect(self._toggle)

        self._back_btn = make_toolbar_button(LABEL_CLOSE_MAP, variant=BTN_ACCENT)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(users_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._count_lbl, 1, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._expand_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._back_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._body_widget = QWidget()
        body_lay = QVBoxLayout(self._body_widget)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(6)
        self._list_layout = QVBoxLayout()
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        body_lay.addWidget(horizontal_divider())
        body_lay.addLayout(self._list_layout)
        self._body_widget.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addWidget(self._body_widget)

        self._refresh_count()

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._body_widget.setVisible(self._expanded)
        chevron = "chevron-up.svg" if self._expanded else "chevron-down.svg"
        self._expand_btn.setIcon(QIcon(tinted_pixmap(chevron, "#9f9fa9", 16)))
        self.toggled.emit()

    def connect_back(self, slot) -> None:
        self._back_btn.clicked.connect(slot)

    def set_total(self, total: int) -> None:
        self._total = total
        self._refresh_count()

    def set_users(self, users: list[dict]) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()
        for entry in users:
            row = _make_user_row(
                entry.get("username", ""), entry.get("role", "viewer"),
            )
            self._list_layout.addWidget(row)
            self._rows.append(row)
        self._online = len(users)
        self._refresh_count()

    def _refresh_count(self) -> None:
        suffix = f"  {self._online}/{self._total}" if self._total else f"  {self._online}"
        self._count_lbl.setText(f"Members{suffix}")
