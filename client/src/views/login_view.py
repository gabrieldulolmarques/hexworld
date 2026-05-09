from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                              QVBoxLayout, QWidget)

class LoginView(QWidget):
    request_login = pyqtSignal(str, str)
    request_register = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        title = QLabel("HexWorld")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")

        self.status_label = QLabel("")

        buttons = QHBoxLayout()
        buttons.addWidget(self.login_button)
        buttons.addWidget(self.register_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.login_button.clicked.connect(self._on_login)
        self.register_button.clicked.connect(self._on_register)

    def _on_login(self):
        username, password = self._get_fields()
        if username and password:
            self.request_login.emit(username, password)

    def _on_register(self):
        username, password = self._get_fields()
        if username and password:
            self.request_register.emit(username, password)

    def _get_fields(self) -> tuple[str, str]:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self.show_message("Fill in all fields.")
        return username, password

    def set_loading(self, loading: bool) -> None:
        self.login_button.setEnabled(not loading)
        self.register_button.setEnabled(not loading)
        self.status_label.setText("Loading..." if loading else "")

    def show_message(self, message: str) -> None:
        self.status_label.setText(message)
