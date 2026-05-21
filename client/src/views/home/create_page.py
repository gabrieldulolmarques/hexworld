"""Create-map form."""

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


class CreatePage(QWidget):
    submit_create = pyqtSignal(str)   # map name
    cancel        = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)
        brand = QLabel("New Map")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Name your new hex map.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(brand)
        header.addWidget(subtitle)

        name_label = QLabel("Map name")
        name_label.setObjectName("fieldLabel")

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(50)
        self.name_input.setPlaceholderText("My hex world")
        self.name_input.returnPressed.connect(self._submit)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        self.confirm_button = QPushButton("Create Map")
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
        card_layout.addWidget(name_label)
        card_layout.addWidget(self.name_input)
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
        """Reset the form and grab focus on the name input."""
        self.name_input.clear()
        self.status_label.setText("")
        self.name_input.setFocus()

    def set_loading(self, loading: bool) -> None:
        self.confirm_button.setEnabled(not loading)
        self.name_input.setEnabled(not loading)
        if loading:
            self.status_label.setText("Creating map…")

    def show_error(self, message: str) -> None:
        set_form_status(self.status_label, message, "error")
        self.set_loading(False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _submit(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            set_form_status(self.status_label, "Map name is required.", "error")
            return
        if len(name) > 50:
            set_form_status(self.status_label, "Map name is too long.", "error")
            return
        self.submit_create.emit(name)
