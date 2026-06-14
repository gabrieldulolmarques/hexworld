from PyQt6.QtWidgets import QWidget

def relayout_after_content_change(widget: QWidget) -> None:
    widget.adjustSize()
    widget.updateGeometry()
    parent = widget.parentWidget()
    if parent is not None:
        layout = parent.layout()
        if layout is not None:
            layout.invalidate()
        parent.adjustSize()
        parent.updateGeometry()
