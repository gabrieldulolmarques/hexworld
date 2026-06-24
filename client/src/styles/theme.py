from resources import assets_path, qss_dir
from styles.colors import QSS_REPLACE

_STYLES_DIR = qss_dir()
_QSS_FILES = ("_base.qss", "_window.qss", "_auth.qss", "_lobby.qss", "_map.qss")

_CHECK_ICON_PATH = assets_path("icons", "check.svg")
_CHECK_ICON_URL = _CHECK_ICON_PATH.resolve().as_posix().replace("\\", "/")

def _load_stylesheet() -> str:
    parts = [(_STYLES_DIR / name).read_text(encoding="utf-8") for name in _QSS_FILES]
    sheet = "\n".join(parts).replace("__CHECK_ICON__", _CHECK_ICON_URL)
    for token, value in QSS_REPLACE.items():
        sheet = sheet.replace(token, value)
    return sheet

STYLESHEET = _load_stylesheet()
