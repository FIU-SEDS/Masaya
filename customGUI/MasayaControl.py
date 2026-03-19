import sys, os, socket
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget, QTabWidget, QComboBox, QGridLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg

class UDPListener(QThread):
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
        self.resize(1333, 800)
        self.setFixedSize(1333, 800)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setMovable(True)
        self.setCentralWidget(self.tabs)

        # All Tabs

        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Main/Schem")

        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "N2 Lines")

        self.tab3 = QWidget()
        self.tabs.addTab(self.tab3, "N2O Lines")

        self.tab4 = QWidget()
        self.tabs.addTab(self.tab4, "IPA Lines")

        self.tab5 = QWidget()
        self.tabs.addTab(self.tab5, "Import")


        label = QLabel(self.tab1)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "PID_Masaya.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1333, 800)
        label.setMaximumSize(1333, 800)

        
        self.name = QLabel("Cold Flow Test", label)
        self.name.setStyleSheet("font-family: 'Consolas'; font: arial; color: white; font-size: 35px; font-weight: bold;")


        self.servoSpeed = QComboBox()
        self.servoSpeed.addItems(["Servo Speed","0.3 Seconds - Fastest", "0.6 Seconds - (Recommended) Moderate Closing Time", "1 Second - Slowest Closing Time"])
        self.servoSpeed.adjustSize()

        self.step1 = QCheckBox("Step1", self.tab1)
        self.step1.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step1.adjustSize()

        self.step2 = QCheckBox("Step2", self.tab1)
        self.step2.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step2.adjustSize()

        self.topLeft = QVBoxLayout()
        self.topLeft.addWidget(self.name)
        self.topLeft.addWidget(self.servoSpeed)
        self.topLeft.addWidget(self.step1)
        self.topLeft.addWidget(self.step2)

        self.topLeftContainer = QWidget(self.tab1)
        self.topLeftContainer.setLayout(self.topLeft)
        self.topLeftContainer.move(18, 10)
        self.topLeftContainer.adjustSize()


        self.statusTitle = QLabel("Status", self.tab1)
        self.statusTitle.setStyleSheet("color: white; font-size: 25px; font-weight: bold;")
        self.statusTitle.adjustSize()

        self.status = QLabel("🔴 DAQ Not Found", self.tab1)
        self.status.setStyleSheet("font-family: 'Consolas'; color: white; font-size: 20px; font-weight: bold;")
        self.status.adjustSize()



        self.topRight = QVBoxLayout()
        self.topRight.addWidget(self.statusTitle)
        self.topRight.addWidget(self.status)
        

        self.topRightContainer = QWidget(self.tab1)
        self.topRightContainer.setLayout(self.topRight)
        self.topRightContainer.move(1050, 10)
        self.topRightContainer.adjustSize()


        self.START = QPushButton("GO", self.tab1)
        self.START.move(18, 658)
        self.START.resize(267, 44)
        self.START.setStyleSheet("""
            QPushButton {
                color: white; 
                font-size: 18px; 
                font-weight: bold; 
                background-color: green;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
        """)
        self.START.clicked.connect(self.GO)

        self.STOP = QPushButton("STOP", self.tab1)
        self.STOP.move(18, 711)
        self.STOP.resize(267, 71)
        self.STOP.setStyleSheet("""
            QPushButton {
                color: white; 
                font-size: 18px; 
                font-weight: bold; 
                background-color: red;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
        self.STOP.clicked.connect(self.STOP_Test)

        label_style = "color: white; font-size: 18px; font-weight: bold;"

        # Load Cells
        self.LC01F = QLabel("-----", label)
        self.LC01F.move(590, 418)
        self.LC01F.setStyleSheet(label_style)
        self.LC01F.adjustSize()

        self.LC02OX = QLabel("-----", label)
        self.LC02OX.move(590, 364)
        self.LC02OX.setStyleSheet(label_style)
        self.LC02OX.adjustSize()
        
        # Thermal Couplers
        self.TC01F = QLabel("-----", label)
        self.TC01F.move(204, 496)
        self.TC01F.setStyleSheet(label_style)
        self.TC01F.adjustSize()

        self.TC02OX = QLabel("-----", label)
        self.TC02OX.move(204, 288)
        self.TC02OX.setStyleSheet(label_style)
        self.TC02OX.adjustSize()

        self.TC03OX = QLabel("-----", label)
        self.TC03OX.move(830, 251)
        self.TC03OX.setStyleSheet(label_style)
        self.TC03OX.adjustSize()

        self.TC02F = QLabel("-----", label)
        self.TC02F.move(827, 530)
        self.TC02F.setStyleSheet(label_style)
        self.TC02F.adjustSize()

        # PT Sensors
        self.PT01F = QLabel("-----", label)
        self.PT01F.move(396, 496)
        self.PT01F.setStyleSheet(label_style)
        self.PT01F.adjustSize()

        self.PT02F = QLabel("-----", label)
        self.PT02F.move(586, 630)
        self.PT02F.setStyleSheet(label_style)
        self.PT02F.adjustSize()

        self.PT03F = QLabel("-----", label)
        self.PT03F.move(787, 630)
        self.PT03F.setStyleSheet(label_style)
        self.PT03F.adjustSize()

        self.PT04F = QLabel("-----", label)
        self.PT04F.move(1052, 530)
        self.PT04F.setStyleSheet(label_style)
        self.PT04F.adjustSize()

        self.PT05E = QLabel("-----", label)
        self.PT05E.move(1208, 452)
        self.PT05E.setStyleSheet(label_style)
        self.PT05E.adjustSize()

        self.PT06OX = QLabel("-----", label)
        self.PT06OX.move(1052, 251)
        self.PT06OX.setStyleSheet(label_style)
        self.PT06OX.adjustSize()

        self.PT07OX = QLabel("-----", label)
        self.PT07OX.move(787, 140)
        self.PT07OX.setStyleSheet(label_style)
        self.PT07OX.adjustSize()

        self.PT08OX = QLabel("-----", label)
        self.PT08OX.move(584, 140)
        self.PT08OX.setStyleSheet(label_style)
        self.PT08OX.adjustSize()

        self.PT09OX = QLabel("-----", label)
        self.PT09OX.move(396, 288)
        self.PT09OX.setStyleSheet(label_style)
        self.PT09OX.adjustSize()



        # Tab 2 Section

        self.TC02OX_graph = pg.PlotWidget()       

        x_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_data = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]

        self.TC02OX_graph.setBackground('k')
        self.TC02OX_graph.setTitle("Temperature over Time", color="b", size="15pt")
        self.TC02OX_graph.setLabel('left', 'Temperature (°C)', color='red', size='12pt')
        self.TC02OX_graph.setLabel('bottom', 'Hour', color='red', size='12pt')
        self.TC02OX_graph.showGrid(x=True, y=True)
        

        pen = pg.mkPen(color=(255, 0, 0), width=3) 
        
        self.TC02OX_graph.plot(x_data, y_data, pen=pen, symbol='o', symbolSize=8, symbolBrush=('b'))


        self.PT09OX_graph = pg.PlotWidget()  

        self.PT09OX_graph.setBackground('k')

        self.TC01F_graph = pg.PlotWidget()  

        self.TC01F_graph.setBackground('k')

        self.PT01F_graph = pg.PlotWidget()  

        self.PT01F_graph.setBackground('k')



        self.n2Charts = QGridLayout(self.tab2)
        self.n2Charts.addWidget(self.TC02OX_graph, 0,0)
        self.n2Charts.addWidget(self.PT09OX_graph, 0,1)
        self.n2Charts.addWidget(self.TC01F_graph, 1,0)
        self.n2Charts.addWidget(self.PT01F_graph, 1,1)


        # Tab 3 Section




        self.udp_thread = UDPListener(ip="192.168.1.100", port=5005)
        self.udp_thread.data_received.connect(self.update_SENSORS)
        self.udp_thread.start()


    def update_SENSORS(self, value):
        self.TC02OX.setText(value)
        self.TC02OX.adjustSize()

    def GO(self):
        if(self.step1.isChecked() and not self.step2.isChecked()):
            self.popUp = QMessageBox(self)
            self.popUp.setWindowTitle("Warning")
            self.popUp.setText("First Step Complete, opening Valves: \n- PT-09-OX\n- PT-01-F\n Second Step isn't complete\nDo the Following: \nMake sure Manual Valves are open\n")
            self.popUp.exec()
        elif(self.step1.isChecked() and self.step2.isChecked()):
            self.popUp = QMessageBox(self)
            self.popUp.setWindowTitle("Warning")
            self.popUp.setText("Third isn't complete\nDo the Following: \nMake sure Manual Valves are open\n")
            self.popUp.exec()
        else:
            self.popUp = QMessageBox(self)
            self.popUp.setWindowTitle("Warning")
            self.popUp.setText("First Step isn't complete\nDo the Following: \nMake sure Manual Valves are open\n")
            self.popUp.exec()

    def STOP_Test(self):
        self.PT01F.setText("STOP")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())