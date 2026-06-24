import sys
from pathlib import Path

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)

def _meipass() -> Path:
    return Path(getattr(sys, "_MEIPASS", "."))

def assets_path(*parts: str) -> Path:
    """Absolute path into the bundled assets/ tree (PyInstaller-aware)."""
    if is_frozen():
        return _meipass().joinpath("assets", *parts)
    return Path(__file__).resolve().parents[1].joinpath("assets", *parts)

def qss_dir() -> Path:
    """Directory holding the .qss stylesheets (PyInstaller-aware)."""
    if is_frozen():
        return _meipass() / "qss"
    return Path(__file__).resolve().parent / "styles" / "qss"
