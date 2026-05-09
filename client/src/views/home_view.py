from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class HomeView(QWidget):
    request_logout = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.welcome_label = QLabel("Welcome!")

        self.status_label = QLabel("")

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.request_logout)

        layout = QVBoxLayout()
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.logout_button)
        self.setLayout(layout)

    def set_user(self, user_id: str) -> None:
        self.welcome_label.setText(f"Welcome, {user_id}!")

    def set_loading(self, loading: bool) -> None:
        self.logout_button.setEnabled(not loading)
        self.status_label.setText("Loading..." if loading else "")

    def show_message(self, message: str) -> None:
        self.status_label.setText(message)
