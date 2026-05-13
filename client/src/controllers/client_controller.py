from controllers.auth_controller import AuthController
from models.login_preferences import LoginPreferences
from models.session import Session
from transport.client import Client
from views.auth_view import AuthView
from views.home_view import HomeView
from views.main_view import MainView

class ClientController:
    def __init__(self, main_view: MainView) -> None:
        self.client = Client()
        self.main_view = main_view
        self.auth_view = AuthView()
        self.home_view = HomeView()
        main_view.stack.addWidget(self.auth_view)
        main_view.stack.addWidget(self.home_view)

        self.session = Session()
        self.preferences = LoginPreferences()
        self._restore_login_preferences()

        self.auth = AuthController(self.client, self.session, self.preferences)
        self._connect_signals()

        if self.session.is_authenticated():
            self.auth.validate_session()

    def _connect_signals(self) -> None:
        self.auth_view.request_login.connect(self.auth.login)
        self.auth_view.request_register.connect(self.auth.register)
        self.home_view.request_logout.connect(self.auth.logout)

        self.auth.login_success.connect(self._show_home)
        self.auth.session_restored.connect(self._show_home)
        self.auth.register_success.connect(self._on_register_success)
        self.auth.logged_out.connect(self._show_auth)
        self.auth.session_expired.connect(self._show_auth)
        self.auth.loading.connect(self._on_loading)
        self.auth.error.connect(self._on_error)

    def _on_loading(self, loading: bool) -> None:
        current = self.main_view.stack.currentWidget()
        if hasattr(current, "set_loading"):
            current.set_loading(loading)

    def _on_error(self, message: str) -> None:
        current = self.main_view.stack.currentWidget()
        if hasattr(current, "show_message"):
            current.show_message(message, level="error")

    def _on_register_success(self) -> None:
        self.auth_view.show_register_success()

    def _show_home(self, user_id: str) -> None:
        self.home_view.set_user(user_id)
        self.main_view.stack.setCurrentWidget(self.home_view)

    def _show_auth(self) -> None:
        self._restore_login_preferences()
        self.auth_view.reset()
        self.main_view.stack.setCurrentWidget(self.auth_view)

    def _restore_login_preferences(self) -> None:
        username, remember = self.preferences.load()
        self.auth_view.set_login_defaults(username, remember)

    def stop(self) -> None:
        self.client.stop()
