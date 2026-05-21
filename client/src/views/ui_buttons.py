"""Factory helpers for consistent push buttons across screens."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QSizePolicy

from styles.ui_constants import (
    BTN_COMPACT_H,
    BTN_COMPACT_W,
    BTN_GHOST,
    BTN_GHOST_COMPACT,
    BTN_PRIMARY,
    BTN_TOOLBAR_H,
    BTN_TOOLBAR_W,

)


def _hand_cursor(btn: QPushButton) -> QPushButton:
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def make_toolbar_button(
    text: str,
    *,
    variant: str = BTN_PRIMARY,
) -> QPushButton:
    """Fixed 120×46 action (home top bar, map navigation)."""
    btn = QPushButton(text)
    btn.setObjectName(variant)
    btn.setFixedSize(BTN_TOOLBAR_W, BTN_TOOLBAR_H)
    return _hand_cursor(btn)


def make_compact_button(
    text: str,
    *,
    variant: str = BTN_GHOST_COMPACT,
) -> QPushButton:
    """Fixed 100×40 secondary action (share page Copy, etc.)."""
    btn = QPushButton(text)
    btn.setObjectName(variant)
    btn.setFixedSize(BTN_COMPACT_W, BTN_COMPACT_H)
    btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return _hand_cursor(btn)


def make_map_card_button(
    text: str,
    *,
    variant: str,
) -> QPushButton:
    """Equal-width action on map list cards (fills 1/3 of the action row)."""
    btn = QPushButton(text)
    btn.setObjectName(variant)
    btn.setFixedHeight(BTN_COMPACT_H)
    btn.setMinimumWidth(0)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    return _hand_cursor(btn)


def make_form_primary_button(text: str) -> QPushButton:
    """Full-width primary CTA inside #card forms and auth."""
    btn = QPushButton(text)
    btn.setObjectName(BTN_PRIMARY)
    btn.setFixedHeight(BTN_TOOLBAR_H)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    return _hand_cursor(btn)


def make_form_ghost_button(text: str) -> QPushButton:
    """Full-width secondary/cancel action inside #card forms."""
    btn = QPushButton(text)
    btn.setObjectName(BTN_GHOST)
    btn.setFixedHeight(BTN_TOOLBAR_H)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    return _hand_cursor(btn)


def make_form_cancel_button(text: str = "Cancel") -> QPushButton:
    """Fixed-width 100×46 ghost paired with a form primary button."""
    btn = QPushButton(text)
    btn.setObjectName(BTN_GHOST)
    btn.setFixedSize(BTN_COMPACT_W, BTN_TOOLBAR_H)
    return _hand_cursor(btn)
