import sys, os, socket
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget
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
        
        try:
            sock.bind((self.ip, self.port))
            print(f"Listening on {self.ip}:{self.port}")
        except OSError as e:
            print(f"Error: Could not bind to {self.ip}:{self.port}. {e}")
            return 

        while True:
            data, addr = sock.recvfrom(1024)
            text = data.decode("utf-8", errors="ignore").strip()
            self.data_received.emit(text)

class DiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Masaya Control")
        self.resize(1500, 900)
        self.setMaximumSize(1500, 900)

        label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "PID_Masaya.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1500, 900)
        label.setMaximumSize(1500, 900)
        self.setCentralWidget(label)

        self.name = QLabel("Cold Flow Test", label)
        self.name.move(20,20)
        self.name.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")


        self.step1 = QCheckBox("Step1",self)
        self.step1.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step1.adjustSize()

        self.step2 = QCheckBox("Step2",self)
        self.step2.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step2.adjustSize()


        self.checkBoxes = QVBoxLayout()
        self.checkBoxes.addWidget(self.step1)
        self.checkBoxes.addWidget(self.step2)

        self.checkBoxContainer = QWidget(self)

        self.checkBoxContainer.setLayout(self.checkBoxes)

        self.checkBoxContainer.move(20, 200)

        self.checkBoxContainer.adjustSize()
        





        self.START = QPushButton("START", self)
        self.START.move(20,740)
        self.START.resize(300,50)
        self.START.setStyleSheet("""
            QPushButton {
                color: white; 
                font-size: 20px; 
                font-weight: bold; 
                background-color: green;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
        """)
        self.START.clicked.connect(self.START_Test)

        self.STOP = QPushButton("STOP", self)
        self.STOP.move(20,800)
        self.STOP.resize(300,80)
        self.STOP.setStyleSheet("""
            QPushButton {
                color: white; 
                font-size: 20px; 
                font-weight: bold; 
                background-color: red;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
        self.STOP.clicked.connect(self.STOP_Test)


        # Load Cells 

        self.LC01F = QLabel("12345", label)
        self.LC01F.move(664,470)
        self.LC01F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.LC01F.adjustSize()

        self.LC02OX = QLabel("12345", label)
        self.LC02OX.move(664,409)
        self.LC02OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.LC02OX.adjustSize()
        
        # Thermal Couplers

        self.TC01F = QLabel("12345", label)
        self.TC01F.move(230,558)
        self.TC01F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.TC01F.adjustSize()

        self.TC02OX = QLabel("12345", label)
        self.TC02OX.move(230,324)
        self.TC02OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.TC02OX.adjustSize()

        self.TC03OX = QLabel("12345", label)
        self.TC03OX.move(934,282)
        self.TC03OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.TC03OX.adjustSize()

        self.TC02F = QLabel("12345", label)
        self.TC02F.move(930,596)
        self.TC02F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.TC02F.adjustSize()

        # PT Sensors

        self.PT01F = QLabel("12345", label)
        self.PT01F.move(446,558)
        self.PT01F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT01F.adjustSize()

        self.PT02F = QLabel("12345", label)
        self.PT02F.move(659,709)
        self.PT02F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT02F.adjustSize()

        self.PT03F = QLabel("12345", label)
        self.PT03F.move(885,709)
        self.PT03F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT03F.adjustSize()

        self.PT04F = QLabel("12345", label)
        self.PT04F.move(1183,596)
        self.PT04F.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT04F.adjustSize()

        self.PT05E = QLabel("12345", label)
        self.PT05E.move(1359,509)
        self.PT05E.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT05E.adjustSize()

        self.PT06OX = QLabel("12345", label)
        self.PT06OX.move(1183,282)
        self.PT06OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT06OX.adjustSize()

        self.PT07OX = QLabel("12345", label)
        self.PT07OX.move(885,157)
        self.PT07OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT07OX.adjustSize()

        self.PT08OX = QLabel("12345", label)
        self.PT08OX.move(657,158)
        self.PT08OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT08OX.adjustSize()

        self.PT09OX = QLabel("12345", label)
        self.PT09OX.move(446,324)
        self.PT09OX.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.PT09OX.adjustSize()



        self.udp_thread = UDPListener(ip="192.168.1.100", port=5005)
        self.udp_thread.data_received.connect(self.update_SENSORS)  
        self.udp_thread.start()

    def update_SENSORS(self, value):
        """Called automatically when new UDP data arrives"""
        self.TC02OX.setText(value)
        self.TC02OX.adjustSize()

    def START_Test(self):
        if(self.step1.isChecked()):
            self.PT01F.setText("Start")
        else:
            self.popUp = QMessageBox(self)
            self.popUp.setWindowTitle("Warning")
            self.popUp.setText("MAKE SURE EVERYTHING IS GOOD")
            self.popUp.exec()

        

    def STOP_Test(self):
        self.PT01F.setText("STOP")

    

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())