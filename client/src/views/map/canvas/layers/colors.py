from PyQt6.QtGui import QColor

def rgba_color(rgb: str, alpha: int) -> QColor:
    r, g, b = (int(part.strip()) for part in rgb.split(","))
    return QColor(r, g, b, alpha)
