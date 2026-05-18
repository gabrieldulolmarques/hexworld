from pathlib import Path

_STYLES_DIR = Path(__file__).resolve().parent / "qss"
_QSS_FILES = ("_base.qss", "_window.qss", "_auth.qss", "_map.qss")

_CHECK_ICON_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "icons" / "check.svg"
)
_CHECK_ICON_URL = _CHECK_ICON_PATH.resolve().as_posix().replace("\\", "/")


def _load_stylesheet() -> str:
    parts = [
        (_STYLES_DIR / name).read_text(encoding="utf-8")
        for name in _QSS_FILES
    ]
    return "\n".join(parts).replace("__CHECK_ICON__", _CHECK_ICON_URL)


STYLESHEET = _load_stylesheet()
