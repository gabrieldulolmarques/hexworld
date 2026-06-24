from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.limits import MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH
from styles.ui_constants import CARD_MARGINS, CARD_SPACING
from views.lobby.helpers import make_card
from views.shared.password_edit import PasswordEdit
from views.shared.ui_buttons import make_form_primary_button
from views.shared.widgets import HexLogo, StatusMixin, horizontal_divider

class AuthView(StatusMixin, QWidget):
    login_requested = pyqtSignal(str, str, bool)
    register_requested = pyqtSignal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("authScreen")
        self._mode = "login"
        self._default_username = ""
        self._default_remember = False
        self._setup_ui()
        self._sync_mode_ui()
        self._apply_login_defaults()

    def _setup_ui(self) -> None:
        card = make_card()

        logo = HexLogo(size=72)

        self.brand = QLabel("HexWorld")
        self.brand.setObjectName("brand")
        self.brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addSpacing(14)
        header.addWidget(self.brand)
        header.addWidget(self.subtitle)

        server_label = QLabel("Server")
        server_label.setObjectName("fieldLabel")
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("host:port")

        username_label = QLabel("Username")
        username_label.setObjectName("fieldLabel")
        self.username_input = QLineEdit()
        self.username_input.setMaxLength(MAX_USERNAME_LENGTH)
        self.username_input.setPlaceholderText("your_username")

        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")
        self.password_input = PasswordEdit()
        self.password_input.setMaxLength(MAX_PASSWORD_LENGTH)

        self.confirm_password_input = PasswordEdit(show_visibility_toggle=False)
        self.confirm_password_input.setMaxLength(MAX_PASSWORD_LENGTH)
        self.confirm_password_input.setPlaceholderText("repeat password")

        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.setObjectName("showPasswordCheckbox")
        self.show_password_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setObjectName("rememberCheckbox")
        self.remember_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.primary_button = make_form_primary_button("Sign in")
        self.primary_button.setDefault(True)
        self.primary_button.setAutoDefault(True)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self._set_status_level("info")

        self.mode_prompt = QLabel("")
        self.mode_prompt.setObjectName("subtitle")
        self.mode_link = QPushButton()
        self.mode_link.setObjectName("link")
        self.mode_link.setCursor(Qt.CursorShape.PointingHandCursor)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        mode_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_row.addWidget(self.mode_prompt)
        mode_row.addWidget(self.mode_link)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(*CARD_MARGINS)
        card_layout.setSpacing(CARD_SPACING)
        card_layout.addLayout(header)
        card_layout.addSpacing(16)
        card_layout.addWidget(server_label)
        card_layout.addWidget(self.server_input)
        card_layout.addSpacing(4)
        card_layout.addWidget(username_label)
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(4)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addWidget(self.show_password_checkbox)
        card_layout.addWidget(self.remember_checkbox)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.primary_button)
        card_layout.addWidget(self.status_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(horizontal_divider())
        card_layout.addSpacing(4)
        card_layout.addLayout(mode_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(0)
        root.addStretch(1)
        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

        self.primary_button.clicked.connect(self._on_primary)
        self.server_input.returnPressed.connect(self._on_primary)
        self.username_input.returnPressed.connect(self._on_primary)
        self.password_input.returnPressed.connect(self._on_primary)
        self.confirm_password_input.returnPressed.connect(self._on_primary)
        self.show_password_checkbox.stateChanged.connect(self._on_show_password_changed)
        self.mode_link.clicked.connect(self._toggle_mode)

    def _sync_mode_ui(self) -> None:
        if self._mode == "login":
            self.brand.setText("HexWorld")
            self.subtitle.setText("Welcome back. Sign in to continue.")
            self.primary_button.setText("Sign in")
            self.username_input.setPlaceholderText("your_username")
            self.password_input.setPlaceholderText("••••••••")
            self.confirm_password_input.hide()
            self.show_password_checkbox.hide()
            self.password_input.set_visibility_toggle_visible(True)
            self.password_input.reset_toggle()
            self.confirm_password_input.clear()
            self.confirm_password_input.reset_toggle()
            self.show_password_checkbox.setChecked(False)
            self.remember_checkbox.show()
            self.mode_prompt.setText("Don't have an account?")
            self.mode_link.setText("Sign up")
        else:
            self.brand.setText("Create account")
            self.subtitle.setText("Start building collaborative hex maps.")
            self.primary_button.setText("Sign up")
            self.username_input.setPlaceholderText("pick a username")
            self.password_input.setPlaceholderText("at least 8 characters")
            self.confirm_password_input.show()
            self.show_password_checkbox.show()
            self.password_input.set_visibility_toggle_visible(False)
            self.password_input.reset_toggle()
            self.confirm_password_input.clear()
            self.confirm_password_input.reset_toggle()
            self.show_password_checkbox.setChecked(False)
            self.remember_checkbox.hide()
            self.mode_prompt.setText("Already have an account?")
            self.mode_link.setText("Sign in")

    def _toggle_mode(self) -> None:
        self._mode = "register" if self._mode == "login" else "login"
        self.username_input.clear()
        self.password_input.clear()
        self.password_input.reset_toggle()
        self.show_message("", level="info")
        self._sync_mode_ui()
        if self._mode == "login":
            self._apply_login_defaults()

    def _on_primary(self) -> None:
        if self._mode == "login":
            self._submit_login()
        else:
            self._submit_register()

    def _submit_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember_me = self.remember_checkbox.isChecked()
        self.login_requested.emit(username, password, remember_me)

    def _on_show_password_changed(self, _state: int) -> None:
        if self._mode != "register":
            return
        checked = self.show_password_checkbox.isChecked()
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_password_input.setEchoMode(mode)

    def _submit_register(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_password_input.text()
        self.register_requested.emit(username, password, confirm)

    def server_address(self) -> str:
        return self.server_input.text().strip()

    def set_server_address(self, address: str) -> None:
        self.server_input.setText(address)

    def set_loading(self, loading: bool) -> None:
        self.primary_button.setEnabled(not loading)
        self.mode_link.setEnabled(not loading)
        self.server_input.setEnabled(not loading)
        self.username_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        self.confirm_password_input.setEnabled(not loading)
        self.show_password_checkbox.setEnabled(not loading)
        self.remember_checkbox.setEnabled(not loading)
        if loading:
            message = "Signing in…" if self._mode == "login" else "Signing up…"
            self.show_message(message, level="info")
        else:
            self.show_message("", level="info")

    def reset(self) -> None:
        self.password_input.clear()
        self.password_input.reset_toggle()
        self.confirm_password_input.clear()
        self.confirm_password_input.reset_toggle()
        self.show_password_checkbox.setChecked(False)
        self.show_message("", level="info")
        self._mode = "login"
        self._sync_mode_ui()
        self._apply_login_defaults()

    def show_register_success(self) -> None:
        self.password_input.clear()
        self.password_input.reset_toggle()
        self.confirm_password_input.clear()
        self.confirm_password_input.reset_toggle()
        self.show_password_checkbox.setChecked(False)
        self._mode = "login"
        self._sync_mode_ui()
        self.show_message("Account created. Please sign in.", level="success")

    def set_login_defaults(self, username: str, remember: bool) -> None:
        self._default_username = username if remember else ""
        self._default_remember = remember
        if self._mode == "login":
            self._apply_login_defaults()

    def _apply_login_defaults(self) -> None:
        self.username_input.setText(self._default_username)
        self.remember_checkbox.setChecked(self._default_remember)
