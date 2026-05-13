from pathlib import Path

_CHECK_ICON_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "icons" / "check.svg"
)
_CHECK_ICON_URL = _CHECK_ICON_PATH.resolve().as_posix().replace("\\", "/")

_STYLESHEET_TEMPLATE = """
* {
    font-family: "Inter", "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
}

QMainWindow#mainView,
QWidget#windowContainer {
    background-color: transparent;
}

QFrame#windowChrome {
    background-color: #09090b;
    border: 1px solid #27272a;
    border-radius: 14px;
}

QFrame#windowChrome[maximized="true"] {
    border: none;
    border-radius: 0;
}

QWidget#root,
QWidget#authScreen,
QStackedWidget {
    background-color: #09090b;
}

/* Login / register: bold UI copy; normal weight only for typed input (QLineEdit). */
QWidget#authScreen QLabel#subtitle {
    font-weight: 600;
}

QWidget#authScreen QLabel#fieldLabel {
    font-weight: 700;
}

QWidget#authScreen QLabel#status {
    font-weight: 600;
}

QWidget#authScreen QLineEdit {
    font-weight: normal;
}

QWidget#authScreen QPushButton {
    font-weight: 700;
}

QWidget#authScreen QCheckBox#rememberCheckbox,
QWidget#authScreen QCheckBox#showPasswordCheckbox {
    color: #9f9fa9;
    font-size: 13px;
    font-weight: 500;
    spacing: 8px;
}

QWidget#authScreen QCheckBox#rememberCheckbox::indicator,
QWidget#authScreen QCheckBox#showPasswordCheckbox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #52525c;
    background-color: #27272a;
}

QWidget#authScreen QCheckBox#rememberCheckbox::indicator:unchecked,
QWidget#authScreen QCheckBox#showPasswordCheckbox::indicator:unchecked {
    image: none;
}

QWidget#authScreen QCheckBox#rememberCheckbox::indicator:checked,
QWidget#authScreen QCheckBox#showPasswordCheckbox::indicator:checked {
    background-color: #5ea500;
    border-color: #5ea500;
    image: url(__CHECK_ICON__);
}

QWidget#authScreen QCheckBox#rememberCheckbox::indicator:checked:hover,
QWidget#authScreen QCheckBox#showPasswordCheckbox::indicator:checked:hover {
    background-color: #497d00;
    border-color: #497d00;
    image: url(__CHECK_ICON__);
}

QWidget#authScreen QCheckBox#rememberCheckbox::indicator:unchecked:hover,
QWidget#authScreen QCheckBox#showPasswordCheckbox::indicator:unchecked:hover {
    border-color: #71717b;
}

QWidget#authScreen QCheckBox#rememberCheckbox:disabled,
QWidget#authScreen QCheckBox#showPasswordCheckbox:disabled {
    color: #71717b;
}

QWidget#card {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 14px;
}

QWidget#titleBar {
    background-color: transparent;
    border-bottom: 1px solid #27272a;
}

QLabel#titleBrand {
    color: #e4e4e7;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.2px;
}

QPushButton#winCtrl,
QPushButton#winClose {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 0;
}

QPushButton#winCtrl:hover {
    background-color: #27272a;
}

QPushButton#winClose:hover {
    background-color: #e7000b;
}

QLabel {
    color: #e4e4e7;
    font-size: 14px;
    background-color: transparent;
}

QLabel#brand {
    color: #e4e4e7;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

QLabel#brandSmall {
    color: #e4e4e7;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel#title {
    color: #e4e4e7;
    font-size: 22px;
    font-weight: 600;
}

QLabel#subtitle {
    color: #9f9fa9;
    font-size: 13px;
}

QLabel#fieldLabel {
    color: #9f9fa9;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

QLabel#status {
    color: #9f9fa9;
    font-size: 12px;
    min-height: 16px;
}

QLabel[level="error"] {
    color: #e7000b;
}

QLabel[level="success"] {
    color: #497d00;
}

QLabel[level="info"] {
    color: #9f9fa9;
}

QLabel#welcome {
    color: #e4e4e7;
    font-size: 26px;
    font-weight: 700;
}

QLabel#userBadge {
    color: #9ae600;
    font-size: 13px;
    font-weight: 600;
    background-color: rgba(94, 165, 0, 0.14);
    border: 1px solid rgba(94, 165, 0, 0.38);
    border-radius: 999px;
    padding: 4px 12px;
}

QLineEdit {
    background-color: #27272a;
    color: #e4e4e7;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: #5ea500;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #5ea500;
    background-color: #27272a;
}

QLineEdit:disabled {
    color: #71717b;
    background-color: #18181b;
}

/* PasswordEdit (pyqt-login-page style): extra trailing padding for QAction icon */
PasswordEdit {
    padding: 10px 40px 10px 14px;
}

QWidget#authScreen PasswordEdit QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px 6px;
    color: #ffffff;
}

QWidget#authScreen PasswordEdit QToolButton:hover {
    background-color: #3f3f46;
    color: #ffffff;
}

QWidget#authScreen PasswordEdit QToolButton:disabled {
    background-color: transparent;
    color: #71717b;
}

QPushButton {
    background-color: #5ea500;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 11px 18px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #497d00;
}

QPushButton:pressed {
    background-color: #3c6300;
}

QPushButton:disabled {
    background-color: #3f3f46;
    color: #9f9fa9;
}

QPushButton#ghost {
    background-color: transparent;
    color: #9f9fa9;
    border: 1px solid #3f3f46;
}

QPushButton#ghost:hover {
    background-color: #18181b;
    border-color: #52525c;
    color: #e4e4e7;
}

QPushButton#ghost:disabled {
    color: #71717b;
    border-color: #27272a;
}

QPushButton#link {
    background-color: transparent;
    color: #7ccf00;
    font-weight: 600;
    border: none;
    padding: 2px 4px;
    text-align: center;
}

QPushButton#link:hover {
    color: #9ae600;
}

QPushButton#link:disabled {
    color: #71717b;
}

QFrame#divider {
    background-color: #27272a;
    max-height: 1px;
    min-height: 1px;
    border: none;
}
"""

STYLESHEET = _STYLESHEET_TEMPLATE.replace("__CHECK_ICON__", _CHECK_ICON_URL)
