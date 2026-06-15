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
    btn = QPushButton(text)
    btn.setObjectName(variant)
    btn.setFixedSize(BTN_TOOLBAR_W, BTN_TOOLBAR_H)
    return _hand_cursor(btn)

def make_compact_button(
    text: str,
    *,
    variant: str = BTN_GHOST_COMPACT,
) -> QPushButton:
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
    btn = QPushButton(text)
    btn.setObjectName(BTN_PRIMARY)
    btn.setFixedHeight(BTN_TOOLBAR_H)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    return _hand_cursor(btn)

def make_form_ghost_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName(BTN_GHOST)
    btn.setFixedHeight(BTN_TOOLBAR_H)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    return _hand_cursor(btn)
