"""Common chrome for the floating map-editor panels."""

from PyQt6.QtWidgets import QWidget

from views.widgets import apply_panel_style, make_card_shadow


def styled(widget: QWidget) -> QWidget:
    """Enable QSS background/border on a panel widget."""
    apply_panel_style(widget)
    return widget


class MapPanel(QWidget):
    """Floating card overlay (same chrome as auth/home #card)."""

    def __init__(self, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        apply_panel_style(self)
        self.setGraphicsEffect(make_card_shadow())
