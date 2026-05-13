from pathlib import Path

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QLineEdit, QWidget

_ICONS_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"

class PasswordEdit(QLineEdit):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        show_visibility_toggle: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("passwordInput")
        self.setEchoMode(QLineEdit.EchoMode.Password)

        self._icon_show = QIcon(str(_ICONS_DIR / "eye.svg"))
        self._icon_hide = QIcon(str(_ICONS_DIR / "eye-off.svg"))

        self._password_shown = False
        self._toggle_action = None
        if show_visibility_toggle:
            self._toggle_action = QAction(self._icon_show, "", self)
            self._toggle_action.setToolTip("Show password")
            self.addAction(self._toggle_action, QLineEdit.ActionPosition.TrailingPosition)
            self._toggle_action.triggered.connect(self._on_toggle_password_action)

    def _on_toggle_password_action(self) -> None:
        if self._toggle_action is None:
            return
        if not self._password_shown:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self._password_shown = True
            self._toggle_action.setIcon(self._icon_hide)
            self._toggle_action.setToolTip("Hide password")
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self._password_shown = False
            self._toggle_action.setIcon(self._icon_show)
            self._toggle_action.setToolTip("Show password")

    def set_visibility_toggle_visible(self, visible: bool) -> None:
        if self._toggle_action is not None:
            self._toggle_action.setVisible(visible)

    def reset_toggle(self) -> None:
        self._password_shown = False
        self.setEchoMode(QLineEdit.EchoMode.Password)
        if self._toggle_action is not None:
            self._toggle_action.setIcon(self._icon_show)
            self._toggle_action.setToolTip("Show password")
