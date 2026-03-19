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

        sensor_configs = [
            ("LC01F", 590, 418), ("LC02OX", 590, 364),
            ("TC01F", 204, 496), ("TC02OX", 204, 288), ("TC03OX", 830, 251), ("TC02F", 827, 530),
            ("PT01F", 396, 496), ("PT02F", 586, 630), ("PT03F", 787, 630), ("PT04F",1052, 530), 
            ("PT05E",1208, 452), ("PT06OX", 1052, 251), ("PT07OX", 787, 140), ("PT08OX",584, 140),
            ("PT09OX",396, 288)

        ]

        self.sensors = {}

        for name, x, y in sensor_configs:
            lbl = QLabel("-----", label)
            lbl.move(x, y)
            lbl.setStyleSheet(label_style)
            lbl.adjustSize()
            self.sensors[name] = lbl



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
        self.sensors["LC01F"].setText(value)
        self.sensors["LC01F"].adjustSize()

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
        self.sensors["PT01F"].setText("STOP")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())