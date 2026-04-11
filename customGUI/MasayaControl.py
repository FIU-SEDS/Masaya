import sys, os, socket, time, MasayaBack
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget, QTabWidget, QComboBox, QGridLayout, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from MasayaBack import DAQComms, CMD_OPEN, CMD_CLOSE_MOD, CMD_CLOSE_SLOW, CMD_CLOSE, CMD_LLT, CMD_TLT
from collections import deque
import pyqtgraph as pg


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
        
        self.dash_title = QLabel("Cold Flow Test", label)
        self.dash_title.setStyleSheet("font-family: 'Consolas'; font: arial; color: white; font-size: 35px; font-weight: bold;")


        self.servoSpeed = QComboBox()
        self.servoSpeed.addItems(["Servo Closing Speed","0.3 Seconds - Fastest", "0.6 Seconds - (Recommended) Moderate", "1 Second - Slowest"])
        self.servoSpeed.adjustSize()

        self.topLeft = QVBoxLayout()
        self.topLeft.setSpacing(30)
        self.topLeft.addWidget(self.dash_title)
        self.topLeft.addWidget(self.servoSpeed)

        checklist_style = "color: white; font-size: 15px; font-weight: bold;"

        checklist_steps = [
            ("Conduct total leak test"),("Conduct localized leak test"), ("Blowdown")
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
                color: black; 
                font-size: 18px; 
                font-weight: bold; 
                background-color: gray;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)

        valve_button_on = ("""
            QPushButton {
                color: black; 
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
            ("BLOWOFF",1285, 450)
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
            gph.max_points = 500

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

        # Comms

        self.comms = DAQComms(
            stm32_ip="192.168.1.200",
            stm32_port=2000,
            listen_port=5005,
            csv_dir="logs"
        )

        self.comms.telemetry_received.connect(self.update_SENSORS)

        self.comms.connection_lost.connect(
            lambda: self.status.setText('<span style="color: red;">●</span> DAQ Not Found')
        )
        self.comms.connection_restored.connect(
            lambda: self.status.setText('<span style="color: green;">●</span> DAQ Connected')
        )

        self.comms.start()


    def update_SENSORS(self, data: dict):
        # 1. Map the UI sensor keys to their corresponding data keys
        sensor_map = {
            # Pressure Transducers
            "PT01F": "PT0", "PT02F": "PT1", "PT04F": "PT2", "PT05E": "PT3",
            "PT06OX": "PT4", "PT07OX": "PT5", "PT08OX": "PT6", "PT09OX": "PT7",
            # Load Cells
            "LC01F": "LC0", "LC02OX": "LC1",
            # Thermocouples
            "TC02OX": "TC0", "TC03OX": "TC1", "TC02F": "TC2"
        }

        # 2. Update Sensor Text Labels
        for ui_key, data_key in sensor_map.items():
            if data_key in data:
                val = data[data_key]
                self.sensors[ui_key].setText(f"{val:.1f}")

        # 3. Update Valve Styles
        valves = ['SEV01F', 'SEV02F', 'SEV03OX', 'SEV04OX', 'SOV01F', 'SOV02OX']
        for valve in valves:
            status = "Opened" if data.get(valve) == 90 else "Closed"
            self.changeValveStyle(valve, status)
        

        # sensor_name = "PT01F" 

        # if sensor_name in self.sensorsGraphs:
        #     self.sensorsGraphs[sensor_name].plot(new_x_data, new_y_data, clear=True)

        # # Need to update PT sensors too
        # if sensor_name in self.ptSensorsGraphs:
        #     self.ptSensorsGraphs[sensor_name].plot(new_x_data, new_y_data, clear=True)
            

    def GO(self):
        total_leak = self.checklist["Conduct total leak test"].isChecked()
        local_leak = self.checklist["Conduct localized leak test"].isChecked()
        blowdown = self.checklist["Blowdown"].isChecked()

        if total_leak and local_leak and blowdown:
            QMessageBox.information(self, "Success", "All tests completed. System ready.")
            return

        if not total_leak:
            reply = QMessageBox.question(
                self, "Warning", 
                "Do you want to conduct a total leak test?\n\nNote: Activates Burping for 900 psig on the following valves and PTs:\n" \
                "SOV-01-F\t--\tPT-02-F\nSOV-02-OX\t--\tPT-08-OX\nPress STOP to stop test.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(4, CMD_TLT)
                pass

        elif not local_leak:
            reply = QMessageBox.question(
                self, "Warning", 
                "Do you want to conduct a local leak test?\n\nNote: Activates Burping for 10 psig on the following valves and PTs:\n" \
                "SOV-01-F\t--\tPT-02-F\nSOV-02-OX\t--\tPT-08-OX",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(4, CMD_LLT)
                pass

        elif not blowdown:
            # Example of the specific text you wanted for the third step
            reply = QMessageBox.question(
                self, "Warning", 
                "Ready to conduct Blowdown?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                pass

    def STOP_Test(self):
        self.comms.send_command(4,CMD_CLOSE)
        self.comms.send_command(5,CMD_CLOSE)
        self.comms.send_command(0,CMD_CLOSE)
        self.comms.send_command(1,CMD_CLOSE)
        self.comms.send_command(2,CMD_CLOSE)
        self.comms.send_command(3,CMD_CLOSE)

    def changeValveStyle(self, valve_name, style):
        valve_button_off = ("""
            QPushButton {
                color: black; 
                font-size: 18px; 
                font-weight: bold; 
                background-color: gray;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)

        valve_button_on = ("""
            QPushButton {
                color: black; 
                font-size: 18px; 
                font-weight: bold; 
                background-color: white;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
            """)
            
        button = self.valves[valve_name]

        if style == "Opened":
            button.setText("Opened")
            button.setStyleSheet(valve_button_on)
        else:
            button.setText("Closed")
            button.setStyleSheet(valve_button_off)



    def valveOC(self, valve_name):
            
        button = self.valves[valve_name]

        VALVE_ID_MAP = {
            "SEV01F":  MasayaBack.SEV01F,
            "SEV02F":  MasayaBack.SEV02F,
            "SEV03OX": MasayaBack.SEV03OX,
            "SEV04OX": MasayaBack.SEV04OX,
            "SOV01F":  MasayaBack.SOV01F,
            "SOV02OX": MasayaBack.SOV02OX,
        }

        selected_speed = self.servoSpeed.currentText()
        
        if button.text() == "Opened":
            closeValve = QMessageBox.question(
                self, # Parent window
                "Confirm Action", # Dialog title
                "Are you sure you want to close this valve?", # Dialog message
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No # Buttons to show
                ) 
            if closeValve == QMessageBox.StandardButton.Yes:
                is_solenoid = valve_name in ("SOV01F", "SOV02OX")
                
                if not is_solenoid and selected_speed == "Servo Closing Speed":
                    QMessageBox.warning(self, "No Speed Selected", "Please select a servo closing speed.")
                    return
            if closeValve == QMessageBox.StandardButton.Yes and (valve_name == "SOV01F" or valve_name == "SOV02OX"):          
                self.changeValveStyle(valve_name, "Closed")
                self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_CLOSE)
            elif closeValve == QMessageBox.StandardButton.Yes and selected_speed == "0.3 Seconds - Fastest":          
                self.changeValveStyle(valve_name, "Closed")
                self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_CLOSE)
            elif closeValve == QMessageBox.StandardButton.Yes and selected_speed == "0.6 Seconds - (Recommended) Moderate":          
                self.changeValveStyle(valve_name, "Closed")
                self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_CLOSE_MOD)
            elif closeValve == QMessageBox.StandardButton.Yes and selected_speed == "1 Second - Slowest":          
                self.changeValveStyle(valve_name, "Closed")
                self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_CLOSE_SLOW)
            
            

        elif button.text() == "Closed":
            openValve = QMessageBox.question(
                self, # Parent window
                "Confirm Action", # Dialog title
                "Are you sure you want to open this valve?", # Dialog message
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No # Buttons to show
                )
            if openValve == QMessageBox.StandardButton.Yes:
                self.changeValveStyle(valve_name, "Opened")
                self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_OPEN)


    def closeEvent(self, event):
        self.comms.stop()
        self.comms.wait()
        event.accept()
           

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())