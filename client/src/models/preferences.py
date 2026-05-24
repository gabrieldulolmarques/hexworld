from PyQt6.QtCore import QSettings

_SETTINGS_ORG = "HexWorld"
_SETTINGS_APP = "HexWorld"
_USERNAME_KEY = "login/username"
_REMEMBER_KEY = "login/remember"

class Preferences:
    def __init__(self) -> None:
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)

    def load(self) -> tuple[str, bool]:
        remember = self._settings.value(_REMEMBER_KEY, False, type=bool)
        username = self._settings.value(_USERNAME_KEY, "", type=str)
        if remember and username:
            return username, True
        return "", False

    def save(self, username: str, remember: bool) -> None:
        if remember:
            self._settings.setValue(_USERNAME_KEY, username)
            self._settings.setValue(_REMEMBER_KEY, True)
            return
        self.clear()

    def clear(self) -> None:
        self._settings.remove(_USERNAME_KEY)
        self._settings.setValue(_REMEMBER_KEY, False)
