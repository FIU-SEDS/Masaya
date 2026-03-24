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
        self.tabs.addTab(self.tab5, "LC/Thrust")

        self.tab6 = QWidget()
        self.tabs.addTab(self.tab6, "Import")

        self.tab7 = QWidget()
        self.tabs.addTab(self.tab7, "Leak Test")


        label = QLabel(self.tab1)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "PID_Masaya.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1333, 800)
        label.setMaximumSize(1333, 800)

        # Main Page top left (Title/Servo Speed/Steps)
        
        self.name = QLabel("Cold Flow Test", label)
        self.name.setStyleSheet("font-family: 'Consolas'; font: arial; color: white; font-size: 35px; font-weight: bold;")


        self.servoSpeed = QComboBox()
        self.servoSpeed.addItems(["Servo Speed","0.3 Seconds - Fastest", "0.6 Seconds - (Recommended) Moderate Closing Time", "1 Second - Slowest Closing Time"])
        self.servoSpeed.adjustSize()

        self.step1 = QCheckBox("Check TC Readings", self.tab1)
        self.step1.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step1.adjustSize()

        self.step2 = QCheckBox("Load cell static readings", self.tab1)
        self.step2.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.step2.adjustSize()

        self.topLeft = QVBoxLayout()
        self.topLeft.addWidget(self.name)
        self.topLeft.addWidget(self.servoSpeed)
        self.topLeft.addWidget(self.step1)
        self.topLeft.addWidget(self.step2)

        self.topLeftContainer = QWidget(self.tab1) # Container that contains top left
        self.topLeftContainer.setLayout(self.topLeft)
        self.topLeftContainer.move(18, 10)
        self.topLeftContainer.adjustSize()

        # Main Page top right (Status)

        self.statusTitle = QLabel("Status", self.tab1)
        self.statusTitle.setStyleSheet("color: white; font-size: 25px; font-weight: bold;")
        self.statusTitle.adjustSize()

        self.status = QLabel('<span style="color: red; font-size: 20pt;">●</span> DAQ Not Found', self.tab1) #HTML TO Make Circle

        self.status.setStyleSheet("font-family: 'Consolas'; color: white; font-size: 20px; font-weight: bold;")
        self.status.adjustSize()

        self.topRight = QVBoxLayout()
        self.topRight.addWidget(self.statusTitle)
        self.topRight.addWidget(self.status)
        
        self.topRightContainer = QWidget(self.tab1) # Container that contains top right
        self.topRightContainer.setLayout(self.topRight)
        self.topRightContainer.move(1050, 10)
        self.topRightContainer.adjustSize()

        # Go and Stop Button Created

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

        # Main Page Schem Labels

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
            lbl.setFixedWidth(80)
            self.sensors[name] = lbl

        # Other Tabs, All Charts 

        self.n2Charts = QGridLayout(self.tab2)
        self.n2oCharts = QGridLayout(self.tab3)
        self.ipaCharts = QGridLayout(self.tab4)
        self.otherCharts = QGridLayout(self.tab5)

        # Easy creation of all charts, contains chart's name/position/x&y grid cords

        sensor_configs_graphs = [
            ("LC01F", self.otherCharts, 0,0), ("LC02OX", self.otherCharts, 0,1),
            ("TC01F", self.n2Charts, 1,0), ("TC02OX", self.n2Charts, 0, 0), ("TC03OX", self.n2oCharts, 1, 0), ("TC02F", self.ipaCharts, 1, 0),
            ("PT01F", self.n2Charts, 1, 1), ("PT02F", self.ipaCharts, 0, 0), ("PT03F", self.ipaCharts, 0, 1), ("PT04F", self.ipaCharts, 1, 1), 
            ("PT05E", self.otherCharts, 0,2), ("PT06OX", self.n2oCharts, 1, 1), ("PT07OX", self.n2oCharts, 0, 1), ("PT08OX",self.n2oCharts, 0, 0),
            ("PT09OX", self.n2Charts, 0, 1)

        ]

        self.sensorsGraphs = {}

        for name, tab, x, y in sensor_configs_graphs:
            gph = pg.PlotWidget()
            gph.setBackground('k')
            gph.setTitle(name, color="w", size="20pt", bold=True)

            #Depending on Sensor type, label changes

            if name[:2] == "TC":
                gph.setLabel('left', 'Temperature (°C)', color='red', size='12pt')
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
            elif name[:2] == "PT":
                gph.setLabel('left', 'Pressure (PSI)', color='red', size='12pt')
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
            elif name[:2] == "LC":
                gph.setLabel('left', 'Grams (PSI)', color='red', size='12pt')
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
            
            tab.addWidget(gph,x,y)

            self.sensorsGraphs[name] = gph
        

        # pen = pg.mkPen(color=(255, 0, 0), width=3) 


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