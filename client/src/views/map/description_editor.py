"""Floating overlay for editing a tile description (markdown source).

Hosted as a child of :class:`views.map.body.MapBody` and covers its full area
with a translucent backdrop and a centered card. Emits ``submitted(q, r, text)``
when the user saves; the backdrop is clickable but does not dismiss (cancel is
explicit via the Cancel button or Esc).
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from views.map.panel import styled
from views.ui_buttons import make_form_ghost_button, make_form_primary_button


class DescriptionEditor(QWidget):
    submitted = pyqtSignal(int, int, str)
    cancelled = pyqtSignal()

    _CARD_W =  1200
    _CARD_MIN_H = 700

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("descriptionEditorBackdrop")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._q = 0
        self._r = 0
        self._setup_ui()
        self._wire_shortcuts()
        self.hide()

    def _setup_ui(self) -> None:
        card = QWidget(self)
        card.setObjectName("descriptionEditorCard")
        styled(card)
        card.setFixedWidth(self._CARD_W)
        card.setMinimumHeight(self._CARD_MIN_H)

        heading = QLabel("DESCRIPTION")
        heading.setObjectName("panelTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._coord = QLabel("")
        self._coord.setObjectName("descriptionEditorCoord")
        self._coord.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._editor = QTextEdit()
        self._editor.setObjectName("descriptionEditorInput")
        self._editor.setPlaceholderText("Write markdown notes for this hex…")
        self._editor.setAcceptRichText(False)
        self._editor.textChanged.connect(self._on_text_changed)

        self._save_btn = make_form_primary_button("Save")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)

        cancel_btn = make_form_ghost_button("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel_btn, 1)
        buttons.addWidget(self._save_btn, 1)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 24)
        card_layout.setSpacing(12)
        card_layout.addWidget(heading)
        card_layout.addWidget(self._coord)
        card_layout.addWidget(self._editor, 1)
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
        save.activated.connect(self._on_save)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_for(self, q: int, r: int, current_text: str = "") -> None:
        self._q = q
        self._r = r
        self._coord.setText(f"Hex ({q}, {r})")
        self._editor.blockSignals(True)
        self._editor.setPlainText(current_text)
        self._editor.blockSignals(False)
        self._on_text_changed()  # sync save button state
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self._editor.setFocus()
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._editor.setTextCursor(cursor)

    def close_editor(self) -> None:
        self._editor.blockSignals(True)
        self._editor.clear()
        self._editor.blockSignals(False)
        self.hide()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_text_changed(self) -> None:
        self._save_btn.setEnabled(bool(self._editor.toPlainText().strip()))

    def _on_save(self) -> None:
        text = self._editor.toPlainText().strip()
        if not text:
            return
        self.submitted.emit(self._q, self._r, text)
        self.close_editor()

    def _on_cancel(self) -> None:
        self.close_editor()
        self.cancelled.emit()
