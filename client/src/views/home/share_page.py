from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from styles.ui_constants import CARD_MARGINS, CARD_SPACING
from views.home.helpers import centered, make_card, set_form_status
from views.ui_buttons import make_compact_button, make_form_ghost_button
from views.widgets import HexLogo

class SharePage(QWidget):
    cancel = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Share")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(brand)
        header.addWidget(self.subtitle)

        hint = QLabel("Invite others with these codes.")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        (
            self.editor_section,
            self.editor_input,
            _,
        ) = self._make_code_section("Editor invite")
        (
            self.viewer_section,
            self.viewer_input,
            _,
        ) = self._make_code_section("Viewer invite")

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        cancel_btn = make_form_ghost_button("Cancel")
        cancel_btn.clicked.connect(self.cancel)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(*CARD_MARGINS)
        card_layout.setSpacing(CARD_SPACING)
        card_layout.addLayout(header)
        card_layout.addSpacing(8)
        card_layout.addWidget(hint)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.editor_section)
        card_layout.addWidget(self.viewer_section)
        card_layout.addWidget(cancel_btn)
        card_layout.addWidget(self.status_label)

        self.editor_section.hide()
        self.viewer_section.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(centered(card))

    def _make_code_section(
        self,
        label_text: str,
    ) -> tuple[QWidget, QLineEdit, QPushButton]:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")

        code_input = QLineEdit()
        code_input.setReadOnly(True)

        copy_btn = make_compact_button("Copy")
        copy_btn.clicked.connect(
            lambda: self._copy_code(code_input, copy_btn),
        )

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(code_input, 1)
        row.addWidget(copy_btn)

        layout.addWidget(label)
        layout.addLayout(row)
        return section, code_input, copy_btn

    def populate(self, data: dict) -> None:
        self.subtitle.setText(data["name"])
        editor_code = data.get("editor_code")
        viewer_code = data.get("viewer_code")

        if editor_code:
            self.editor_input.setText(editor_code)
            self.editor_section.show()
        else:
            self.editor_section.hide()

        if viewer_code:
            self.viewer_input.setText(viewer_code)
            self.viewer_section.show()
        else:
            self.viewer_section.hide()

        if editor_code or viewer_code:
            self.status_label.setText("")
        else:
            set_form_status(
                self.status_label,
                "You do not have permission to view share codes for this map.",
                "info",
            )

    @staticmethod
    def _copy_code(code_input: QLineEdit, button: QPushButton) -> None:
        code = code_input.text().strip()
        if not code:
            return
        QGuiApplication.clipboard().setText(code)
        previous = button.text()
        button.setText("Copied!")

        def restore() -> None:
            button.setText(previous)

        QTimer.singleShot(1500, restore)
