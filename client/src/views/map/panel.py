from PyQt6.QtWidgets import QWidget

from views.widgets import apply_panel_style, make_card_shadow

def styled(widget: QWidget) -> QWidget:
    apply_panel_style(widget)
    return widget

class MapPanel(QWidget):

    def __init__(self, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        apply_panel_style(self)
        self.setGraphicsEffect(make_card_shadow())
