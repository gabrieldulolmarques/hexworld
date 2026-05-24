"""Floating overlay for exporting the current map to PNG."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from views.map.panel import styled
from views.ui_buttons import make_form_ghost_button, make_form_primary_button


class ExportDialog(QWidget):
    submitted = pyqtSignal(str)
    cancelled = pyqtSignal()

    _CARD_W = 680

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("exportDialogBackdrop")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()
        self._wire_shortcuts()
        self.hide()

    def _setup_ui(self) -> None:
        card = QWidget(self)
        card.setObjectName("exportDialogCard")
        styled(card)
        card.setFixedWidth(self._CARD_W)

        heading = QLabel("EXPORT MAP")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        path_label = QLabel("PNG FILE")
        path_label.setObjectName("fieldLabel")

        self._path_input = QLineEdit()
        self._path_input.setObjectName("exportDialogPath")
        self._path_input.textChanged.connect(self._sync_export_enabled)

        self._status = QLabel("")
        self._status.setObjectName("status")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._set_status("", "info")

        cancel_btn = make_form_ghost_button("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)

        self._export_btn = make_form_primary_button("Export")
        self._export_btn.clicked.connect(self._on_export)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel_btn, 1)
        buttons.addWidget(self._export_btn, 1)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(14)
        card_layout.addWidget(heading)
        card_layout.addSpacing(2)
        card_layout.addWidget(path_label)
        card_layout.addWidget(self._path_input)
        card_layout.addWidget(self._status)
        card_layout.addLayout(buttons)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)
        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)

    def _wire_shortcuts(self) -> None:
        esc = QShortcut(QKeySequence("Esc"), self)
        esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        esc.activated.connect(self._on_cancel)

        save = QShortcut(QKeySequence("Ctrl+Return"), self)
        save.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        save.activated.connect(self._on_export)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_for(self, default_path: str) -> None:
        self._path_input.setText(default_path)
        self._set_status("", "info")
        self._sync_export_enabled()
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self._path_input.setFocus()
        self._path_input.selectAll()

    def set_busy(self, busy: bool) -> None:
        self._path_input.setEnabled(not busy)
        self._export_btn.setEnabled(not busy and bool(self._path_input.text().strip()))
        if busy:
            self._set_status("Exporting...", "info")

    def show_success(self, path: str) -> None:
        self.set_busy(False)
        self._set_status(f"Export complete: {path}", "success")

    def show_error(self, message: str) -> None:
        self.set_busy(False)
        self._set_status(message, "error")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _sync_export_enabled(self) -> None:
        self._export_btn.setEnabled(bool(self._path_input.text().strip()))

    def _on_export(self) -> None:
        path = self._path_input.text().strip()
        if not path:
            self._set_status("Enter a PNG file path.", "error")
            return
        self.submitted.emit(path)

    def _on_cancel(self) -> None:
        self.hide()
        self.cancelled.emit()

    def _set_status(self, text: str, level: str) -> None:
        self._status.setText(text)
        self._status.setProperty("level", level)
        style = self._status.style()
        style.unpolish(self._status)
        style.polish(self._status)
