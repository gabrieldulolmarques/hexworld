from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from styles.ui_constants import (
    BTN_MAP_CARD_DANGER,
    BTN_MAP_CARD_GHOST,
    BTN_MAP_CARD_OPEN,
    LABEL_OPEN_MAP,
    MAP_CARD_ACTION_GAP,
    MAP_CARD_MARGIN_H,
    MAP_CARD_WIDTH,
)
from views.ui_buttons import make_map_card_button

CARD_WIDTH = MAP_CARD_WIDTH
CARD_HEIGHT = 200

def _format_date(raw: str) -> str:
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return raw

class MapCard(QFrame):
    open_clicked       = pyqtSignal(str)
    share_clicked      = pyqtSignal(str)
    dissociate_clicked = pyqtSignal(str)
    delete_clicked     = pyqtSignal(str)

    def __init__(self, data: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mapCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._map_id       = data["id"]
        self._role         = data["role"]
        self._member_count = data["member_count"]
        self.setProperty("role", self._role)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._setup_ui(data)

    def _setup_ui(self, data: dict) -> None:
        name_label = QLabel()
        name_label.setObjectName("mapName")
        name_label.setToolTip(data["name"])
        metrics = QFontMetrics(name_label.font())
        name_label.setText(
            metrics.elidedText(
                data["name"],
                Qt.TextElideMode.ElideRight,
                CARD_WIDTH - 96,
            )
        )

        role_label = QLabel(f"● {self._role.capitalize()}")
        role_label.setObjectName("mapRole")
        role_label.setProperty("role", self._role)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(name_label, 1)
        header.addWidget(role_label, 0, Qt.AlignmentFlag.AlignTop)

        count = data["member_count"]
        members_text = "1 member" if count == 1 else f"{count} members"
        meta = QLabel(f"{members_text}  ·  {_format_date(data['created_at'])}")
        meta.setObjectName("mapMeta")

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)

        open_btn = make_map_card_button(LABEL_OPEN_MAP, variant=BTN_MAP_CARD_OPEN)
        open_btn.clicked.connect(lambda: self.open_clicked.emit(self._map_id))

        share_btn = make_map_card_button("Share", variant=BTN_MAP_CARD_GHOST)
        share_btn.clicked.connect(lambda: self.share_clicked.emit(self._map_id))

        is_solo_owner = self._role == "owner" and self._member_count == 1
        if is_solo_owner:
            action_btn = make_map_card_button("Delete", variant=BTN_MAP_CARD_DANGER)
            action_btn.clicked.connect(lambda: self.delete_clicked.emit(self._map_id))
        else:
            action_btn = make_map_card_button("Dissociate", variant=BTN_MAP_CARD_GHOST)
            action_btn.clicked.connect(lambda: self.dissociate_clicked.emit(self._map_id))

        actions = QHBoxLayout()
        actions.setSpacing(MAP_CARD_ACTION_GAP)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(open_btn, 1)
        actions.addWidget(share_btn, 1)
        actions.addWidget(action_btn, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            MAP_CARD_MARGIN_H, 18, MAP_CARD_MARGIN_H, 16,
        )
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addWidget(meta)
        layout.addSpacing(6)
        layout.addWidget(divider)
        layout.addSpacing(2)
        layout.addLayout(actions)
