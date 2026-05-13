from sys import argv, exit

from PyQt6.QtWidgets import QApplication

from controllers.client_controller import ClientController
from styles.theme import STYLESHEET
from views.main_view import MainView

def main() -> None:
    app = QApplication(argv)
    app.setStyleSheet(STYLESHEET)

    window = MainView()
    controller = ClientController(window)
    window.show()

    result = app.exec()
    controller.stop()
    exit(result)

if __name__ == "__main__":
    main()
