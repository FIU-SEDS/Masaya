import sys, os
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class DiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Piping Diagram")
        self.resize(1280, 720)

        label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "PID.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1280, 720)
        self.setCentralWidget(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())