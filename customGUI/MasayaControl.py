import sys, os, socket
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget, QTabWidget, QComboBox, QGridLayout, QMessageBox
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
        self.resize(1600, 900)
        self.setFixedSize(1600, 900)

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
        self.tabs.addTab(self.tab6, "PT Sensors")


        label = QLabel(self.tab1)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        label.setPixmap(QPixmap(os.path.join(script_dir, "assets", "final_PID.png")))
        label.setScaledContents(True)
        label.setMinimumSize(1580, 900)
        label.setMaximumSize(1580, 900)
        label.adjustSize()

        # Main Page top left (Title/Servo Speed/Steps)
        
        self.name = QLabel("Cold Flow Test", label)
        self.name.setStyleSheet("font-family: 'Consolas'; font: arial; color: white; font-size: 35px; font-weight: bold;")


        self.servoSpeed = QComboBox()
        self.servoSpeed.addItems(["Servo Speed","0.3 Seconds - Fastest", "0.6 Seconds - (Recommended) Moderate Closing Time", "1 Second - Slowest Closing Time"])
        self.servoSpeed.adjustSize()

        self.topLeft = QVBoxLayout()
        self.topLeft.setSpacing(30)
        self.topLeft.addWidget(self.name)
        self.topLeft.addWidget(self.servoSpeed)

        checklist_style = "color: white; font-size: 15px; font-weight: bold;"

        checklist_steps = [
            ("Check TC Readings"), ("Check LC static readings"), ("Check valve protocals"),
            ("Check LC readings while filling"),("Conduct leak test"), ("Check PT readings"),
            ("Check Depressurization System"),("Conduct localized leak test"), ("Blowdown")

        ]

        self.checklist = {}

        for name in checklist_steps:
            chk = QCheckBox(name)
            chk.setStyleSheet(checklist_style)
            self.topLeft.addWidget(chk)
            self.checklist[name] = chk


        self.topLeftContainer = QWidget(self.tab1) # Container that contains top left
        self.topLeftContainer.setLayout(self.topLeft)
        self.topLeftContainer.move(18, 10)
        self.topLeftContainer.adjustSize()

        # Main Page top right (Status)

        self.statusTitle = QLabel("Status", self.tab1)
        self.statusTitle.setStyleSheet("color: white; font-size: 25px; font-weight: bold;")
        self.statusTitle.adjustSize()

        status_style = "font-family: 'Consolas'; color: white; font-size: 20px; font-weight: bold;"

        self.status = QLabel('<span style="color: red; font-size: 20pt;">●</span> DAQ Not Found', self.tab1) #HTML TO Make Circle
        self.sensor_status = QLabel('<span style="color: red; font-size: 20pt;">●</span> Sensors NaN', self.tab1) #HTML TO Make Circle
        self.status.setStyleSheet(status_style)
        self.sensor_status.setStyleSheet(status_style)
        self.status.adjustSize()

        self.topRight = QVBoxLayout()
        self.topRight.addWidget(self.statusTitle)
        self.topRight.addWidget(self.status)
        self.topRight.addWidget(self.sensor_status)
        
        self.topRightContainer = QWidget(self.tab1) # Container that contains top right
        self.topRightContainer.setLayout(self.topRight)
        self.topRightContainer.move(1250, 10)
        self.topRightContainer.adjustSize()

        # Go and Stop Button Created

        self.START = QPushButton("GO", self.tab1)
        self.START.move(18, 758)
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
        self.STOP.move(18, 811)
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

        # Servo/Solenoid Button Creation

        valve_button_off = ("""
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

        valve_button_on = ("""
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

        valve_configs = [
            ("SEV01F", 610, 650), ("SEV02F", 1085, 650), 
            ("SEV03OX", 1085, 335),("SEV04OX", 610, 335),
            ("SOV01F", 850, 853),("SOV02OX", 850, 96),

        ]

        self.valves = {}

        for name, x, y in valve_configs:
            but = QPushButton("Closed", label)
            but.move(x, y)
            but.setStyleSheet(valve_button_off)
            but.resize(100, 25)
            self.valves[name] = but
            but.clicked.connect(lambda checked=False, v_name=name: self.valveOC(v_name))

        # Main Page Schem Labels

        sensor_label_style = "color: white; font-size: 20px; font-weight: bold;"


        sensor_configs = [
            ("LC01F", 625, 487), ("LC02OX", 625, 420),
            ("TC01F", 970, 820), ("TC02OX", 970, 60), ("TC03OX", 962, 290), ("TC02F", 960, 607),
            ("PT01F", 450, 607), ("PT02F", 630, 752), ("PT04F",1240, 607), 
            ("PT05E",1440, 530), ("PT06OX", 1240, 290), ("PT07OX", 890, 147), ("PT08OX", 630, 147),
            ("PT09OX", 450, 290),
            ("WW_n2o", 780, 268), ("WW_ipa", 780, 579),
            ("MFR_ipa", 773, 332), ("MFR_ipa", 773, 650)

        ]

        self.sensors = {}

        for name, x, y in sensor_configs:
            lbl = QLabel("-----", label)
            lbl.move(x, y)
            lbl.setStyleSheet(sensor_label_style)
            lbl.setFixedWidth(80)
            self.sensors[name] = lbl

        # Other Tabs, All Charts 

        self.n2Charts = QGridLayout(self.tab2)
        self.n2oCharts = QGridLayout(self.tab3)
        self.ipaCharts = QGridLayout(self.tab4)
        self.otherCharts = QGridLayout(self.tab5)
        self.ptSensors = QGridLayout(self.tab6)

        # Easy creation of all charts, contains chart's name/position/x&y grid cords

        sensor_configs_graphs = [
            ("LC01F", self.otherCharts, 0,0), ("LC02OX", self.otherCharts, 0,1),
            ("TC01F", self.n2Charts, 1,0), ("TC02OX", self.n2Charts, 0, 0), ("TC03OX", self.n2oCharts, 1, 0), ("TC02F", self.ipaCharts, 1, 0),
            ("PT01F", self.n2Charts, 1, 1), ("PT02F", self.ipaCharts, 0, 0), ("PT04F", self.ipaCharts, 1, 1), 
            ("PT05E", self.otherCharts, 0,2), ("PT06OX", self.n2oCharts, 1, 1), ("PT07OX", self.n2oCharts, 0, 1), ("PT08OX",self.n2oCharts, 0, 0),
            ("PT09OX", self.n2Charts, 0, 1)

        ]

        self.sensorsGraphs = {}
        self.ptSensorsGraphs = {}

        pt_row = 0
        pt_col = 0
        max_cols = 4 

        for name, tab, x, y in sensor_configs_graphs:
            gph = pg.PlotWidget()
            gph.setBackground('k')
            gph.setTitle(name, color="w", size="20pt", bold=True)

            if name[:2] == "TC":
                gph.setLabel('left', 'Temperature (°C)', color='red', size='12pt')
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
            elif name[:2] == "PT":
                gph.setLabel('left', 'Pressure (PSI)', color='red', size='12pt')
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
                
                gph_duplicate = pg.PlotWidget()
                gph_duplicate.setBackground('k')
                gph_duplicate.setTitle(name, color="w", size="20pt", bold=True)
                gph_duplicate.setLabel('left', 'Pressure (PSI)', color='red', size='12pt')
                gph_duplicate.setLabel('bottom', 'Hour', color='red', size='12pt')
                
                self.ptSensors.addWidget(gph_duplicate, pt_row, pt_col)
                self.ptSensorsGraphs[name] = gph_duplicate
                
                pt_col += 1
                if pt_col >= max_cols:
                    pt_col = 0
                    pt_row += 1

            elif name[:2] == "LC":
                gph.setLabel('left', 'Kilograms (Kg)', color='red', size='12pt') 
                gph.setLabel('bottom', 'Hour', color='red', size='12pt')
            
            tab.addWidget(gph, x, y)
            self.sensorsGraphs[name] = gph

        # pen = pg.mkPen(color=(255, 0, 0), width=3) 


        # Tab 3 Section


        self.udp_thread = UDPListener(ip="192.168.1.100", port=5005)
        self.udp_thread.data_received.connect(self.update_SENSORS)
        self.udp_thread.start()





    def update_SENSORS(self, value):
        self.sensors["LC01F"].setText(value)
        self.sensors["LC01F"].adjustSize()
        
        # sensor_name = "PT01F" 

        # if sensor_name in self.sensorsGraphs:
        #     self.sensorsGraphs[sensor_name].plot(new_x_data, new_y_data, clear=True)

        # # Need to update PT sensors too
        # if sensor_name in self.ptSensorsGraphs:
        #     self.ptSensorsGraphs[sensor_name].plot(new_x_data, new_y_data, clear=True)
            

    def GO(self):
        if(self.checklist["Check TC Readings"].isChecked() and not self.checklist["Check LC static readings"].isChecked()):
            self.popUp = QMessageBox(self)
            self.popUp.setWindowTitle("Warning")
            self.popUp.setText("Check TC Readings Test Complete, opening Valves: \n- PT-09-OX\n- PT-01-F\n Check LC static readings isn't complete\nDo the Following: \nMake sure Manual Valves are open\n")
            self.popUp.exec()
        elif(self.checklist["Check TC Readings"].isChecked() and self.checklist["Check LC static readings"].isChecked()):
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

    def valveOC(self, valve_name):
        valve_button_off = ("""
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

        valve_button_on = ("""
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
            
        button = self.valves[valve_name]
        
        if button.text() == "Closed":
            openValve = QMessageBox.question(
                self, # Parent window
                "Confirm Action", # Dialog title
                "Are you sure you want to open this valve?", # Dialog message
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No # Buttons to show
                ) 
            if openValve == QMessageBox.StandardButton.Yes:          
                button.setText("Open")
                button.setStyleSheet(valve_button_on)

        elif button.text() == "Open":
            closeValve = QMessageBox.question(
                self, # Parent window
                "Confirm Action", # Dialog title
                "Are you sure you want to close this valve?", # Dialog message
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No # Buttons to show
                )
            if closeValve == QMessageBox.StandardButton.Yes:
                button.setText("Closed")
                button.setStyleSheet(valve_button_off)

        
           

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())