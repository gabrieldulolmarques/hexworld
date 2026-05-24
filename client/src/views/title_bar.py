from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from styles.colors import RED_PRIMARY
from views.widgets import HexLogo

class _CtrlButton(QPushButton):
    BG_NORMAL = QColor("#09090b")
    BG_HOVER = QColor("#27272a")
    BG_CLOSE_HOVER = QColor(RED_PRIMARY)

    def __init__(self, kind: str) -> None:
        super().__init__()
        self._kind = kind
        self.setObjectName("winClose" if kind == "close" else "winCtrl")
        self.setFlat(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(38, 30)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._sync_tooltip()

    def set_kind(self, kind: str) -> None:
        if kind != self._kind:
            self._kind = kind
            self._sync_tooltip()
            self.update()

    def _sync_tooltip(self) -> None:
        labels = {
            "min": "Minimize",
            "max": "Maximize",
            "restore": "Restore",
            "close": "Close",
        }
        self.setToolTip(labels[self._kind])

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        hovered = self.underMouse()
        is_close = self._kind == "close"
        bg = (
            self.BG_CLOSE_HOVER if (hovered and is_close)
            else self.BG_HOVER if hovered
            else self.BG_NORMAL
        )
        if hovered and is_close:
            line_color = QColor("#ffffff")
        elif hovered:
            line_color = QColor("#e4e4e7")
        else:
            line_color = QColor("#9f9fa9")

        pen = QPen(line_color)
        pen.setWidthF(1.4)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = self.width() / 2, self.height() / 2
        s = 4.5

        if self._kind == "min":
            painter.drawLine(int(cx - s), int(cy), int(cx + s), int(cy))
        elif self._kind == "max":
            painter.drawRect(int(cx - s), int(cy - s), int(s * 2), int(s * 2))
        elif self._kind == "restore":
            offset = 1.6
            painter.drawRect(
                int(cx - s + offset), int(cy - s - offset), int(s * 2), int(s * 2)
            )
            front = (
                int(cx - s - offset), int(cy - s + offset), int(s * 2), int(s * 2)
            )
            painter.fillRect(front[0], front[1], front[2], front[3], bg)
            painter.drawRect(*front)
        elif self._kind == "close":
            painter.drawLine(int(cx - s), int(cy - s), int(cx + s), int(cy + s))
            painter.drawLine(int(cx - s), int(cy + s), int(cx + s), int(cy - s))

class WindowTitleBar(QWidget):
    HEIGHT = 42

    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self.setObjectName("titleBar")
        self.setFixedHeight(self.HEIGHT)
        self._setup_ui()

    def _setup_ui(self) -> None:
        logo = HexLogo(size=20)
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        brand = QLabel("HexWorld")
        brand.setObjectName("titleBrand")
        brand.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.minimize_button = _CtrlButton("min")
        self.maximize_button = _CtrlButton("max")
        self.close_button = _CtrlButton("close")

        self.minimize_button.clicked.connect(self._window.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximize)
        self.close_button.clicked.connect(self._window.close)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 6, 5)
        layout.setSpacing(8)
        layout.addWidget(logo)
        layout.addWidget(brand)
        layout.addStretch(1)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

    def update_maximize_glyph(self) -> None:
        self.maximize_button.set_kind(
            "restore" if self._window.isMaximized() else "max"
        )

    def _toggle_maximize(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        window = self._window
        handle = window.windowHandle()
        if handle is None:
            window.winId()
            handle = window.windowHandle()
        if handle is not None:
            handle.startSystemMove()

        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
