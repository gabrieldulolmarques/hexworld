from os import getenv

from PyQt6.QtCore import QSettings

_KEY = "connection/ns_address"
_DEV_DEFAULT = "127.0.0.1:9090"

class ServerConfig:
    """Persists the Pyro Name Server address from the login screen.

    Resolution order: PYRO_NS_HOST (+ PYRO_NS_PORT) env > PYRO_NS_ADDRESS env
    > saved value > 127.0.0.1:9090."""

    def __init__(self) -> None:
        self._settings = QSettings()

    def load(self) -> str:
        host = getenv("PYRO_NS_HOST")
        if host:
            port = getenv("PYRO_NS_PORT", "9090")
            return f"{host}:{port}"
        env = getenv("PYRO_NS_ADDRESS")
        if env:
            return env
        saved = self._settings.value(_KEY, "", type=str)
        if saved:
            return saved
        return _DEV_DEFAULT

    def save(self, address: str) -> None:
        address = address.strip()
        if address:
            self._settings.setValue(_KEY, address)

def parse_ns_address(raw: str) -> tuple[str, int]:
    host, _, port = raw.rpartition(":")
    if not host or not port or not port.isdigit():
        raise ValueError(f"Invalid Name Server address '{raw}', expected 'host:port'")
    return host, int(port)
