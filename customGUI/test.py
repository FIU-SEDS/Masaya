import sys, os, socket
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class UDPListener(QThread):
    # Signal that sends the received string to the main thread
    data_received = pyqtSignal(str)

    def __init__(self, ip="192.168.1.100", port=5005):
        super().__init__()
        self.ip = ip
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.ip, self.port))
        print(f"Listening on {self.ip}:{self.port}")

        while True:
            data, addr = sock.recvfrom(1024)
            text = data.decode("utf-8", errors="ignore").strip()
            self.data_received.emit(text)  


class DiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Piping Diagram")
        self.resize(1280, 720)

        label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "PID_2.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1280, 720)
        self.setCentralWidget(label)

        self.pressure = QLabel("--", label)
        self.pressure.move(194, 274)
        self.pressure.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        self.pressure.adjustSize()

        self.udp_thread = UDPListener(ip="192.168.1.100", port=5005)
        self.udp_thread.data_received.connect(self.update_pressure)  
        self.udp_thread.start()

    def update_pressure(self, value):
        """Called automatically when new UDP data arrives"""
        self.pressure.setText(value)
        self.pressure.adjustSize()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())