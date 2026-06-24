from os import getenv

from PyQt6.QtCore import QSettings

from resources import is_frozen

_KEY = "connection/server_address"
DEMO_SERVER_ADDRESS = "hexworld.playit.plus:1048"
_DEV_DEFAULT = "127.0.0.1:5000"

class ServerConfig:
    """Persists the server address the user picks on the login screen.

    Resolution order: SERVER_ADDRESS env > saved value > built-in default
    (the public demo when frozen, localhost in development)."""

    def __init__(self) -> None:
        self._settings = QSettings()

    def load(self) -> str:
        env = getenv("SERVER_ADDRESS")
        if env:
            return env
        saved = self._settings.value(_KEY, "", type=str)
        if saved:
            return saved
        return DEMO_SERVER_ADDRESS if is_frozen() else _DEV_DEFAULT

    def save(self, address: str) -> None:
        address = address.strip()
        if address:
            self._settings.setValue(_KEY, address)
