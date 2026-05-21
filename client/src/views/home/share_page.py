"""Share-map page — shows editor / viewer invite codes."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
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


class SharePage(QWidget):
    cancel = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)
        brand = QLabel("Share Map")
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
            self.editor_copy,
        ) = self._make_code_section("Editor invite")
        (
            self.viewer_section,
            self.viewer_input,
            self.viewer_copy,
        ) = self._make_code_section("Viewer invite")

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.cancel)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 28)
        card_layout.setSpacing(10)
        card_layout.addLayout(header)
        card_layout.addSpacing(8)
        card_layout.addWidget(hint)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.editor_section)
        card_layout.addWidget(self.viewer_section)
        card_layout.addWidget(self.status_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(cancel_btn)

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

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("ghost")
        copy_btn.setProperty("shareCopy", "true")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

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
