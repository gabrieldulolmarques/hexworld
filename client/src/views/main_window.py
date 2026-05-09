from PyQt6.QtWidgets import QMainWindow, QStackedWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HexWorld")
        self.resize(300, 180)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
