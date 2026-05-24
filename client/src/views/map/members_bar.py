from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

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
    geometry_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("mapBottomBar")
        self._expanded = True
        self._rows: list[QWidget] = []
        self._row_names: list[tuple[QLabel, QLabel, str]] = []
        self._online = 0
        self._total = 0
        self._height_budget: int | None = None
        self._last_bar_width = 0
        self._layout_changing = False

        users_icon = QLabel()
        users_icon.setPixmap(tinted_pixmap("users.svg", "#9f9fa9", 18))
        users_icon.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self._title_lbl = QLabel("Members")
        self._title_lbl.setObjectName("onlinePanelTitle")
        self._title_lbl.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred,
        )

        self._ratio_lbl = QLabel("")
        self._ratio_lbl.setObjectName("onlinePanelRatio")
        self._ratio_lbl.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred,
        )
        self._ratio_lbl.hide()

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
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        header.addWidget(users_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._title_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._ratio_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addStretch(1)
        header.addWidget(self._expand_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._back_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._header_widget = QWidget()
        self._header_widget.setLayout(header)
        self._header_widget.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )

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
        body_lay.setSpacing(4)
        body_lay.addWidget(horizontal_divider())
        body_lay.addWidget(self._scroll)
        self._body_widget.setVisible(self._expanded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 9, 16, 9)
        layout.setSpacing(6)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self._header_widget)
        layout.addWidget(self._body_widget)

        self.setMaximumWidth(MEMBERS_BAR_MAX_W)
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Maximum,
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_row_elides()

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._body_widget.setVisible(self._expanded)
        chevron = "chevron-up.svg" if self._expanded else "chevron-down.svg"
        self._expand_btn.setIcon(QIcon(tinted_pixmap(chevron, "#9f9fa9", 16)))
        self._update_list_height()
        self._apply_header_width()
        self._notify_geometry()

    def connect_back(self, slot) -> None:
        self._back_btn.clicked.connect(slot)

    def set_total(self, total: int) -> None:
        self._total = max(0, total)
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

    def apply_height_budget(self, budget: int) -> int:
        self._height_budget = max(0, budget)
        self._update_list_height()
        return self.natural_height()

    def natural_height(self) -> int:
        chrome = self._chrome_height()
        if not self._expanded:
            return chrome
        return chrome + self._scroll.height()

    def _chrome_height(self) -> int:
        margins = 18
        header = self._header_widget.sizeHint().height()
        if not self._expanded:
            return margins + header
        body_lay = self._body_widget.layout()
        extra = body_lay.spacing() + 1 if body_lay is not None else 5
        return margins + header + extra

    def _max_list_height(self) -> int | None:
        if self._height_budget is None:
            return None
        return max(0, self._height_budget - self._chrome_height())

    def _notify_geometry(self) -> None:
        if self._layout_changing:
            return
        self.geometry_changed.emit()

    def _list_content_height(self, count: int) -> int:
        if count <= 0:
            return 0
        return count * MEMBERS_ROW_H + (count - 1) * MEMBERS_ROW_GAP

    def _scroll_viewport_cap(self) -> int:
        visible = (
            MEMBERS_VISIBLE_ROWS * MEMBERS_ROW_H
            + (MEMBERS_VISIBLE_ROWS - 1) * MEMBERS_ROW_GAP
        )
        cap = self._max_list_height()
        if cap is not None:
            return min(visible, cap)
        return visible

    def _update_list_height(self) -> None:
        if not self._expanded:
            self._scroll.setFixedHeight(0)
            return

        count = len(self._rows)
        content_h = self._list_content_height(count)

        if count < MEMBERS_SCROLL_THRESHOLD:
            list_h = content_h
            scroll_policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            list_h = min(content_h, self._scroll_viewport_cap())
            scroll_policy = Qt.ScrollBarPolicy.ScrollBarAsNeeded

        cap = self._max_list_height()
        if cap is not None:
            list_h = min(list_h, cap)

        self._layout_changing = True
        try:
            self._scroll.setFixedHeight(list_h)
            self._scroll.setVerticalScrollBarPolicy(scroll_policy)
        finally:
            self._layout_changing = False
        self._apply_row_elides()

    def _refresh_count(self) -> None:
        if self._total > 0:
            self._ratio_lbl.setText(f"{self._online}/{self._total}")
            self._ratio_lbl.setToolTip(
                f"{self._online} online, {self._total} members in this map",
            )
            self._ratio_lbl.show()
        elif self._online > 0:
            self._ratio_lbl.setText(str(self._online))
            self._ratio_lbl.setToolTip(f"{self._online} online")
            self._ratio_lbl.show()
        else:
            self._ratio_lbl.hide()
            self._ratio_lbl.setToolTip("")
        self._apply_header_width(notify=True)

    def _apply_header_width(self, *, notify: bool = False) -> None:
        self._header_widget.adjustSize()
        margins = 32
        header_w = self._header_widget.sizeHint().width()
        bar_w = min(max(header_w + margins, 200), MEMBERS_BAR_MAX_W)
        if bar_w != self._last_bar_width:
            self._last_bar_width = bar_w
            self.setFixedWidth(bar_w)
            self.adjustSize()
            notify = True
        if notify:
            self._notify_geometry()

    def _inner_width(self) -> int:
        inner = self.width() - 32
        return min(max(inner, 0), MEMBERS_BAR_MAX_W - 32)

    def _apply_row_elides(self) -> None:
        from PyQt6.QtGui import QFontMetrics

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
