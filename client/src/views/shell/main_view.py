from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from views.shell.title_bar import WindowTitleBar
from views.shared.widgets import hex_logo_icon

class MainView(QMainWindow):
    SHADOW_MARGIN = 10

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HexWorld")
        self.setWindowIcon(hex_logo_icon())
        self.setObjectName("mainView")
        self.setMinimumSize(960, 600)
        self.resize(1280, 800)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.title_bar = WindowTitleBar(self)
        self.stack = QStackedWidget()

        self._connection_banner = QLabel()
        self._connection_banner.setObjectName("connectionBanner")
        self._connection_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._connection_banner.setMinimumHeight(44)
        self._connection_banner.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        self._connection_banner.hide()

        self._window_container = QWidget()
        self._window_container.setObjectName("windowContainer")
        self._window_container.setMouseTracking(True)

        self._window_chrome = QFrame()
        self._window_chrome.setObjectName("windowChrome")

        self._window_shadow = QGraphicsDropShadowEffect(self._window_chrome)
        self._window_shadow.setBlurRadius(32)
        self._window_shadow.setOffset(0, 10)
        self._window_shadow.setColor(QColor(0, 0, 0, 150))
        self._window_chrome.setGraphicsEffect(self._window_shadow)

        container_layout = QVBoxLayout(self._window_container)
        container_layout.setContentsMargins(
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN,
        )
        container_layout.setSpacing(0)
        container_layout.addWidget(self._window_chrome)

        layout = QVBoxLayout(self._window_chrome)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.title_bar)
        layout.addWidget(self._connection_banner)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(self._window_container)

        self._sync_window_chrome()

    def show_connection_status(self, message: str | None) -> None:
        if message:
            self._connection_banner.setText(message)
            self._connection_banner.show()
            return
        self._connection_banner.hide()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.update_maximize_glyph()
            self._sync_window_chrome()
        super().changeEvent(event)

    def _sync_window_chrome(self) -> None:
        maximized = self.isMaximized() or self.isFullScreen()
        margin = 0 if maximized else self.SHADOW_MARGIN
        self._window_container.layout().setContentsMargins(
            margin, margin, margin, margin
        )
        self._window_shadow.setEnabled(not maximized)
        self._window_chrome.setProperty("maximized", "true" if maximized else "false")
        self._window_chrome.style().unpolish(self._window_chrome)
        self._window_chrome.style().polish(self._window_chrome)
        self._window_chrome.update()
