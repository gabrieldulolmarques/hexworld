from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from styles.ui_constants import CARD_MARGINS, CARD_SPACING
from views.lobby.helpers import centered, make_card, set_form_status
from views.shared.ui_buttons import make_form_ghost_button, make_form_primary_button
from views.shared.widgets import HexLogo

class JoinPage(QWidget):
    join_submitted = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Join")
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

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("xxxx-xxxx")
        self.code_input.returnPressed.connect(self._submit)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        self.confirm_button = make_form_primary_button("Join")
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self._submit)

        cancel_btn = make_form_ghost_button("Cancel")
        cancel_btn.clicked.connect(self.cancelled)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel_btn, 1)
        buttons.addWidget(self.confirm_button, 1)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(*CARD_MARGINS)
        card_layout.setSpacing(CARD_SPACING)
        card_layout.addLayout(header)
        card_layout.addSpacing(16)
        card_layout.addWidget(code_label)
        card_layout.addWidget(self.code_input)
        card_layout.addSpacing(8)
        card_layout.addLayout(buttons)
        card_layout.addWidget(self.status_label)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(centered(card))

    def focus(self) -> None:
        self.code_input.clear()
        self.status_label.setText("")
        self.code_input.setFocus()

    def set_loading(self, loading: bool) -> None:
        self.confirm_button.setEnabled(not loading)
        self.code_input.setEnabled(not loading)
        if loading:
            self.status_label.setText("Joining map…")

    def show_error(self, message: str) -> None:
        set_form_status(self.status_label, message, "error")
        self.set_loading(False)

    def _submit(self) -> None:
        code = self.code_input.text().strip()
        if not code:
            set_form_status(self.status_label, "Invite code is required.", "error")
            return
        self.join_submitted.emit(code)
