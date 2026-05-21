"""Bottom-left card — collapsible online-members list and Close Map button."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from styles.ui_constants import BTN_ACCENT, LABEL_CLOSE_MAP
from views.map.constants import (
    MEMBERS_BAR_MAX_W,
    MEMBERS_ROW_GAP,
    MEMBERS_ROW_H,
    MEMBERS_SCROLL_THRESHOLD,
    MEMBERS_VISIBLE_ROWS,
)
from views.map.icons import tinted_pixmap
from views.map.panel import MapPanel
from views.ui_buttons import make_toolbar_button
from views.widgets import horizontal_divider


def _make_user_row(username: str, role: str) -> tuple[QWidget, QLabel, QLabel]:
    row = QWidget()
    row.setFixedHeight(MEMBERS_ROW_H)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    bullet = QLabel("●")
    bullet.setObjectName("mapRole")
    bullet.setProperty("role", role)

    name_lbl = QLabel(username)
    name_lbl.setObjectName("onlinePanelUser")
    name_lbl.setMinimumWidth(0)
    name_lbl.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred,
    )

    role_lbl = QLabel(f"[{role.capitalize()}]")
    role_lbl.setObjectName("mapRole")
    role_lbl.setProperty("role", role)

    layout.addWidget(bullet)
    layout.addWidget(name_lbl, 1)
    layout.addWidget(role_lbl, 0)
    return row, name_lbl, role_lbl


class MembersBar(MapPanel):
    toggled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("mapBottomBar")
        self._expanded = False
        self._rows: list[QWidget] = []
        self._row_names: list[tuple[QLabel, QLabel, str]] = []
        self._online = 0
        self._total = 0
        self._max_panel_height: int | None = None
        self._max_list_height: int | None = None

        users_icon = QLabel()
        users_icon.setPixmap(tinted_pixmap("users.svg", "#9f9fa9", 18))

        self._count_lbl = QLabel("Members")
        self._count_lbl.setObjectName("onlinePanelTitle")
        self._count_lbl.setMinimumWidth(0)
        self._count_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

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

        self._header_widget = QWidget()
        self._header_widget.setLayout(header)

        self._list_host = QWidget()
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(MEMBERS_ROW_GAP)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("membersScroll")
        self._scroll.setWidget(self._list_host)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        self._body_widget = QWidget()
        body_lay = QVBoxLayout(self._body_widget)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(6)
        body_lay.addWidget(horizontal_divider())
        body_lay.addWidget(self._scroll)
        self._body_widget.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(self._header_widget)
        layout.addWidget(self._body_widget)
        self.setMaximumWidth(MEMBERS_BAR_MAX_W)
        self.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Maximum,
        )

        self._refresh_count()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_count_elide()
        self._apply_row_elides()

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._body_widget.setVisible(self._expanded)
        chevron = "chevron-up.svg" if self._expanded else "chevron-down.svg"
        self._expand_btn.setIcon(QIcon(tinted_pixmap(chevron, "#9f9fa9", 16)))
        self._update_list_height()
        self.adjustSize()
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
        self._row_names.clear()
        for entry in users:
            username = entry.get("username", "")
            role = entry.get("role", "viewer")
            row, name_lbl, role_lbl = _make_user_row(username, role)
            self._list_layout.addWidget(row)
            self._rows.append(row)
            self._row_names.append((name_lbl, role_lbl, username))
        self._online = len(users)
        self._refresh_count()
        self._update_list_height()
        self._apply_row_elides()
        self.adjustSize()

    def set_max_panel_height(self, height: int) -> None:
        """Cap panel growth so it stops below the tool strip (MapBody)."""
        self._max_panel_height = max(0, height)
        self._max_list_height = max(0, height - self._chrome_height())
        self._update_list_height()
        self.setMaximumHeight(self._max_panel_height)
        self.adjustSize()

    def _chrome_height(self) -> int:
        margins = 12 + 12
        header = self._header_widget.sizeHint().height()
        if not self._expanded:
            return margins + header
        return margins + header + 8 + 7  # header–body gap + divider block

    def _list_content_height(self, count: int) -> int:
        if count <= 0:
            return 0
        return count * MEMBERS_ROW_H + (count - 1) * MEMBERS_ROW_GAP

    def _scroll_viewport_cap(self) -> int:
        visible = (
            MEMBERS_VISIBLE_ROWS * MEMBERS_ROW_H
            + (MEMBERS_VISIBLE_ROWS - 1) * MEMBERS_ROW_GAP
        )
        if self._max_list_height is not None:
            return min(visible, self._max_list_height)
        return visible

    def _update_list_height(self) -> None:
        if not self._expanded:
            self.adjustSize()
            return

        count = len(self._rows)
        content_h = self._list_content_height(count)

        if count < MEMBERS_SCROLL_THRESHOLD:
            list_h = content_h
            scroll_policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            list_h = min(content_h, self._scroll_viewport_cap())
            scroll_policy = Qt.ScrollBarPolicy.ScrollBarAsNeeded

        if self._max_list_height is not None:
            list_h = min(list_h, self._max_list_height)

        self._scroll.setFixedHeight(list_h)
        self._scroll.setVerticalScrollBarPolicy(scroll_policy)
        self._apply_row_elides()
        self.adjustSize()

    def _count_full_text(self) -> str:
        if self._total:
            return f"Members  {self._online}/{self._total}"
        return f"Members  {self._online}"

    def _count_display_text(self) -> str:
        return self._count_full_text()

    def _apply_count_elide(self) -> None:
        display = self._count_display_text()
        full = self._count_full_text()
        avail = self._count_lbl.width()
        if avail < 8:
            header_w = self._header_widget.width()
            if header_w > 0:
                reserved = (
                    18 + self._expand_btn.width() + self._back_btn.width() + 40
                )
                avail = max(48, header_w - reserved)
            else:
                avail = 160
        metrics = QFontMetrics(self._count_lbl.font())
        elided = metrics.elidedText(display, Qt.TextElideMode.ElideRight, avail)
        self._count_lbl.setText(elided)
        self._count_lbl.setToolTip(full if display != full else "")

    def _inner_width(self) -> int:
        inner = self.width() - 32
        return min(max(inner, 0), MEMBERS_BAR_MAX_W - 32)

    def _apply_row_elides(self) -> None:
        inner_w = self._inner_width()
        if inner_w < 24:
            return
        metrics = QFontMetrics(self.font())
        for name_lbl, role_lbl, username in self._row_names:
            role_w = role_lbl.sizeHint().width()
            name_w = max(24, inner_w - role_w - 20)
            elided = metrics.elidedText(
                username, Qt.TextElideMode.ElideRight, name_w,
            )
            name_lbl.setText(elided)
            name_lbl.setToolTip(username if elided != username else "")

    def _refresh_count(self) -> None:
        self._apply_count_elide()
