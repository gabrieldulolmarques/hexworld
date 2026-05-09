from sys import argv, exit

from PyQt6.QtWidgets import QApplication

from controllers.client_controller import ClientController
from views.main_window import MainWindow

def main() -> None:
    app = QApplication(argv)

    window = MainWindow()
    try:
        controller = ClientController(window)
    except Exception:
        exit(1)

    window.show()

    result = app.exec()
    controller.stop()
    exit(result)

if __name__ == "__main__":
    main()
