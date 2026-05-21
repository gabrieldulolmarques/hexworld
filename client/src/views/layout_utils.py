"""Helpers for Qt layouts that must reflow after async data arrives.

Qt layouts compute size hints at build time. When text or counts are set later
(network response, etc.), call relayout_after_content_change() so widgets pick up
the new sizeHint before the parent positions them.

See: QLayout.sizeConstraint (SetFixedSize / SetMinimumSize) in Qt docs.
"""

from PyQt6.QtWidgets import QLayout, QWidget


def relayout_after_content_change(widget: QWidget) -> None:
    """Recalculate size hints from the widget up through its parents."""
    widget.adjustSize()
    widget.updateGeometry()
    parent = widget.parentWidget()
    if parent is not None:
        layout = parent.layout()
        if layout is not None:
            layout.invalidate()
        parent.adjustSize()
        parent.updateGeometry()
