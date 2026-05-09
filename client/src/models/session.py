from json import dump, load
from os import getenv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value)


def _session_path() -> Path:
    custom_path = getenv("HEXWORLD_SESSION_PATH")
    if custom_path:
        return Path(custom_path).expanduser()

    client_id = getenv("CLIENT_ID")
    if client_id:
        return DATA_DIR / f"session-{_safe_filename(client_id)}.json"

    return DATA_DIR / "session.json"


class Session:
    def __init__(self):
        self.path = _session_path()
        self.token: str | None = None
        self.user_id: str | None = None  # memory only
        self._load()

    def save(self, token: str) -> None:
        self.token = token
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            dump({"token": token}, f)

    def set_user_id(self, user_id: str) -> None:
        self.user_id = user_id

    def clear(self) -> None:
        self.token = None
        self.user_id = None
        if self.path.exists():
            self.path.unlink()

    def is_authenticated(self) -> bool:
        return self.token is not None

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path) as f:
                self.token = load(f).get("token")
        except Exception:
            self.clear()
