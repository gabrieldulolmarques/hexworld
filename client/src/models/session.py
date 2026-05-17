from json import dump, load
from os import getenv
from pathlib import Path

class Session:
    def __init__(self) -> None:
        self.path: Path = _get_session_path()
        self.token: str | None = None
        self.user_id: str | None = None
        self.username: str | None = None
        self._load()

    def save(self, token: str) -> None:
        self.token = token
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            dump({"token": token}, f)

    def set_user(self, user_id: str, username: str) -> None:
        self.user_id = user_id
        self.username = username

    def clear(self) -> None:
        self.token = None
        self.user_id = None
        self.username = None
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

def _get_session_path() -> Path:
    configured = getenv("SESSION_PATH")
    if configured:
        return Path(configured)
    client_id = getenv("CLIENT_ID", "1")
    return Path(__file__).resolve().parents[2] / "data" / f"session_{client_id}.json"
