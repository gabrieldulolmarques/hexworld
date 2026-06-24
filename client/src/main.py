import logging
from sys import argv, exit

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

    window = MainView()
    controller = ClientApp(window)
    window.show()

    result = app.exec()
    controller.stop()
    exit(result)

if __name__ == "__main__":
    main()
