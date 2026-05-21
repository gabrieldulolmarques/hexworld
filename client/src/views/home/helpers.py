"""Small helpers shared across the home sub-pages."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from views.widgets import apply_panel_style, make_card_shadow


def make_card(width: int = 360) -> QWidget:
    """Return a styled #card widget used by the auxiliary form pages."""
    card = QWidget()
    card.setObjectName("card")
    apply_panel_style(card)
    card.setFixedWidth(width)
    card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
    card.setGraphicsEffect(make_card_shadow())
    return card


def centered(widget: QWidget) -> QWidget:
    """Wrap a widget so it stays vertically centered with side padding."""
    body = QWidget()
    layout = QVBoxLayout(body)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(0)
    layout.addStretch(1)
    layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
    layout.addStretch(1)
    return body


def set_form_status(label: QLabel, text: str, level: str) -> None:
    """Update a status QLabel and re-polish so QSS picks up the level property."""
    label.setText(text)
    label.setProperty("level", level)
    label.style().unpolish(label)
    label.style().polish(label)
