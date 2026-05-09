from PyQt6.QtWidgets import QMessageBox

from communication.client import Client
from controllers.auth_controller import AuthController
from models.session import Session
from views.home_view import HomeView
from views.login_view import LoginView
from views.main_window import MainWindow

class ClientController:
    def __init__(self, main_window: MainWindow):
        self.main_window = main_window
        self.login_view = LoginView()
        self.home_view = HomeView()
        main_window.stack.addWidget(self.login_view)
        main_window.stack.addWidget(self.home_view)

        self.session = Session()
        self.client = Client()
        try:
            self.client.start()
        except Exception as exception:
            QMessageBox.critical(main_window, "Connection Error", str(exception))
            raise

        self.auth = AuthController(self.client, self.session)
        self._connect_signals()

        if self.session.is_authenticated():
            self.auth.validate_session()

    def _connect_signals(self) -> None:
        self.login_view.request_login.connect(self.auth.login)
        self.login_view.request_register.connect(self.auth.register)
        self.home_view.request_logout.connect(self.auth.logout)

        self.auth.login_success.connect(self._show_home)
        self.auth.session_restored.connect(self._show_home)
        self.auth.register_success.connect(
            lambda: self.login_view.show_message("Registrado! Faça o login.")
        )
        self.auth.logged_out.connect(self._show_login)
        self.auth.loading.connect(self._on_loading)
        self.auth.error.connect(self._on_error)

    def _on_loading(self, loading: bool) -> None:
        current = self.main_window.stack.currentWidget()
        if hasattr(current, "set_loading"):
            current.set_loading(loading)

    def _on_error(self, message: str) -> None:
        if message == "Sessão expirada.":
            self._show_login()
        current = self.main_window.stack.currentWidget()
        if hasattr(current, "show_message"):
            current.show_message(message)

    def _show_home(self, user_id: str) -> None:
        self.home_view.set_user(user_id)
        self.main_window.stack.setCurrentWidget(self.home_view)

    def _show_login(self) -> None:
        self.main_window.stack.setCurrentWidget(self.login_view)

    def stop(self) -> None:
        self.client.stop()
