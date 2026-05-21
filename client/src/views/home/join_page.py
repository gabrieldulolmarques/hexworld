"""Join-map form."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from views.home.helpers import centered, make_card, set_form_status
from views.widgets import HexLogo


class JoinPage(QWidget):
    submit_join = pyqtSignal(str)   # invite code
    cancel      = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Join Map")
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

        self.confirm_button = QPushButton("Join Map")
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self._submit)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.cancel)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self.confirm_button)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 28)
        card_layout.setSpacing(10)
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _submit(self) -> None:
        code = self.code_input.text().strip()
        if not code:
            set_form_status(self.status_label, "Invite code is required.", "error")
            return
        self.submit_join.emit(code)
