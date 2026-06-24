from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap

from resources import assets_path

ICONS_DIR = assets_path("icons")

def tinted_pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    px = QIcon(str(ICONS_DIR / name)).pixmap(QSize(size, size))
    tinted = QPixmap(px.size())
    tinted.fill(Qt.GlobalColor.transparent)
    p = QPainter(tinted)
    p.drawPixmap(0, 0, px)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(tinted.rect(), QColor(color))
    p.end()
    return tinted
