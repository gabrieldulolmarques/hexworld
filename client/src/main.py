import logging
import signal
from sys import argv, exit

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app import ClientApp
from styles.theme import STYLESHEET
from views.shell.main_view import MainView
from views.shared.widgets import hex_logo_icon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

def main() -> None:
    app = QApplication(argv)
    app.setOrganizationName("HexWorld")
    app.setApplicationName("HexWorld")
    app.setWindowIcon(hex_logo_icon())
    app.setStyleSheet(STYLESHEET)

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    sigint_timer = QTimer()
    sigint_timer.timeout.connect(lambda: None)
    sigint_timer.start(200)

    window = MainView()
    controller = ClientApp(window)
    window.show()

    result = app.exec()
    controller.stop()
    exit(result)

if __name__ == "__main__":
    main()
