import sys, os, socket, time, MasayaBack
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget, QTabWidget, QComboBox, QGridLayout, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from MasayaBack import DAQComms, CMD_OPEN, CMD_CLOSE_MOD, CMD_CLOSE_SLOW, CMD_CLOSE, CMD_LLT, CMD_TLT
from collections import deque
import pyqtgraph as pg
import numpy as np


class DiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.blowdown_active   = False
        self.lc_stable_count   = 0
        self.lc_last_value     = None
        self.blowdown_timer    = QTimer()
        self.blowdown_timer.timeout.connect(self.blowdown_tick)


        self.blowdown_timer.setInterval(100)  # check every 100ms
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
            ("Conduct total leak test"),("Conduct localized leak test"), ("Press Tanks"), ("Blowdown")
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
        self.status.setStyleSheet(status_style)
        self.sensor_status.setStyleSheet(status_style)
        self.status.adjustSize()

        self.topRight = QVBoxLayout()
        self.topRight.addWidget(self.statusTitle)
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
            ("Downstream",1085, 450), ("Upstream",485, 450)
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
                gph.setLabel('bottom', 'Time (s)', color='red', size='12pt')
            elif name[:2] == "PT":
                gph.setLabel('left', 'Pressure (PSI)', color='red', size='12pt')
                gph.setLabel('bottom', 'Time (s)', color='red', size='12pt')
                
                gph_duplicate = pg.PlotWidget()
                gph_duplicate.setBackground('k')
                gph_duplicate.setTitle(name, color="w", size="20pt", bold=True)
                gph_duplicate.setLabel('left', 'Pressure (PSI)', color='red', size='12pt')
                gph_duplicate.setLabel('bottom', 'Time (s)', color='red', size='12pt')
                
                self.ptSensors.addWidget(gph_duplicate, pt_row, pt_col)
                self.ptSensorsGraphs[name] = gph_duplicate
                
                pt_col += 1
                if pt_col >= max_cols:
                    pt_col = 0
                    pt_row += 1

            elif name[:2] == "LC":
                gph.setLabel('left', 'Kilograms (Kg)', color='red', size='12pt') 
                gph.setLabel('bottom', 'Time (s)', color='red', size='12pt')
            
            tab.addWidget(gph, x, y)
            self.sensorsGraphs[name] = gph

        # ── Graph data buffers ─────────────────────────────────────────────────
        # Keeps 30 seconds of data at 100Hz = 3000 points max per sensor.
        # update_SENSORS() buffers at 100Hz; update_graphs() redraws at 20Hz.

        HISTORY_S  = 30
        MAX_POINTS = HISTORY_S * 100

        self.t_start     = time.monotonic()
        self.graph_times = deque(maxlen=MAX_POINTS)

        # All sensor UI names that have a PlotWidget
        graph_sensor_names = [
            "LC01F", "LC02OX",
            "TC01F", "TC02OX", "TC03OX", "TC02F",
            "PT01F", "PT02F", "PT04F", "PT05E",
            "PT06OX", "PT07OX", "PT08OX", "PT09OX",
        ]
        self.graph_data = {name: deque(maxlen=MAX_POINTS) for name in graph_sensor_names}

        # Maps UI sensor name → telemetry data key (same as sensor_map in update_SENSORS)
        self.graph_key_map = {
            "PT01F": "PT0", "PT02F": "PT1", "PT04F": "PT2", "PT05E": "PT3",
            "PT06OX": "PT4", "PT07OX": "PT5", "PT08OX": "PT6", "PT09OX": "PT7",
            "LC01F": "LC0", "LC02OX": "LC1",
            "TC01F": "TC0", "TC02OX": "TC0", "TC03OX": "TC1", "TC02F": "TC2",
        }

        # Pre-create one curve per PlotWidget so we call setData() instead of plot()
        # which avoids allocating a new curve object every frame.
        self.graph_curves     = {}   # main tab curves  {ui_name: PlotDataItem}
        self.graph_curves_pt  = {}   # PT tab duplicate curves {ui_name: PlotDataItem}

        for name in graph_sensor_names:
            if name in self.sensorsGraphs:
                self.graph_curves[name] = self.sensorsGraphs[name].plot(
                    pen=pg.mkPen('y', width=2)
                )
            if name in self.ptSensorsGraphs:
                self.graph_curves_pt[name] = self.ptSensorsGraphs[name].plot(
                    pen=pg.mkPen('c', width=2)
                )

        # Redraw timer — 20Hz is smooth enough for live data
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_graphs)
        self.plot_timer.start(50)

        # ── Comms ──────────────────────────────────────────────────────────────

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

        # 4. Buffer graph data — runs at 100Hz, no drawing here
        t = time.monotonic() - self.t_start
        self.graph_times.append(t)

        for ui_name, data_key in self.graph_key_map.items():
            if data_key in data:
                self.graph_data[ui_name].append(data[data_key])
        

        lc_list = list(self.graph_data["LC01F"])
        t_list  = list(self.graph_times)

        if len(lc_list) >= 20:  # need enough points for a meaningful fit
            # Grab last 20 points (~2 seconds of data at 100Hz)
            y = np.array(lc_list[-20:])
            t = np.array(t_list[-20:])
            
            # Fit a degree-1 polynomial (straight line) → y = m*t + b
            coeffs = np.polyfit(t, y, 1)
            mfr = coeffs[0]  # slope in g/s, negative as tank empties


    def update_graphs(self):
        """Called every 50ms (20Hz) by plot_timer. Pushes buffered data to all curves."""
        if not self.graph_times:
            return

        t = list(self.graph_times)
        x_min = t[-1] - 30  # scroll to show last 30 seconds

        for name, curve in self.graph_curves.items():
            y = list(self.graph_data[name])
            if not y:
                continue
            # Trim t to match y length in case they diverge briefly at startup
            t_trimmed = t[-len(y):]
            curve.setData(t_trimmed, y)
            self.sensorsGraphs[name].setXRange(x_min, t[-1], padding=0)

        # Also update the duplicate PT charts in tab6
        for name, curve in self.graph_curves_pt.items():
            y = list(self.graph_data[name])
            if not y:
                continue
            t_trimmed = t[-len(y):]
            curve.setData(t_trimmed, y)
            self.ptSensorsGraphs[name].setXRange(x_min, t[-1], padding=0)

    def GO(self):
        total_leak = self.checklist["Conduct total leak test"].isChecked()
        local_leak = self.checklist["Conduct localized leak test"].isChecked()
        press_tank = self.checklist["Press Tank"].isChecked()
        blowdown = self.checklist["Blowdown"].isChecked()

        if total_leak and local_leak and blowdown and press_tank:
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

        elif not local_leak:
            reply = QMessageBox.question(
                self, "Warning", 
                "Do you want to conduct a local leak test?\n\nNote: Activates Burping for 10 psig on the following valves and PTs:\n" \
                "SOV-01-F\t--\tPT-02-F\nSOV-02-OX\t--\tPT-08-OX\nPress STOP to stop test.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(4, CMD_LLT)

        elif not press_tank:
            reply = QMessageBox.question(
                self, "Warning", 
                "Do you want to start pressurizing tanks?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(0, CMD_OPEN)
                self.comms.send_command(3, CMD_OPEN)

        elif not blowdown:
            reply = QMessageBox.question(
                self, "Warning", 
                "Ready to conduct Blowdown?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(1, CMD_OPEN)
                self.comms.send_command(2, CMD_OPEN)
                self.blowdown_active  = True
                self.lc_stable_count  = 0
                self.lc_last_value    = None
                self.blowdown_timer.start()
                            
                                  

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
        selected_speed = self.servoSpeed.currentText()

        GROUP_MAP = {
            "Upstream":   ["SEV01F", "SEV04OX"],
            "Downstream": ["SEV02F", "SEV03OX"],
        }

        VALVE_ID_MAP = {
            "SEV01F":  MasayaBack.SEV01F,
            "SEV02F":  MasayaBack.SEV02F,
            "SEV03OX": MasayaBack.SEV03OX,
            "SEV04OX": MasayaBack.SEV04OX,
            "SOV01F":  MasayaBack.SOV01F,
            "SOV02OX": MasayaBack.SOV02OX,
        }

        # --- Group buttons (Upstream / Downstream) ---
        if valve_name in GROUP_MAP:
            if button.text() == "Closed":
                if QMessageBox.question(self, "Confirm Action",
                        f"Are you sure you want to open {valve_name} valves?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    ) != QMessageBox.StandardButton.Yes:
                    return

                for v in GROUP_MAP[valve_name]:
                    self.changeValveStyle(v, "Opened")
                    self.comms.send_command(VALVE_ID_MAP[v], CMD_OPEN)
                self.changeValveStyle(valve_name, "Opened")

            elif button.text() == "Opened":
                if QMessageBox.question(self, "Confirm Action",
                        f"Are you sure you want to close {valve_name} valves?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    ) != QMessageBox.StandardButton.Yes:
                    return

                if selected_speed == "Servo Closing Speed":
                    QMessageBox.warning(self, "No Speed Selected", "Please select a servo closing speed.")
                    return

                if selected_speed == "0.3 Seconds - Fastest":
                    cmd = CMD_CLOSE
                elif selected_speed == "0.6 Seconds - (Recommended) Moderate":
                    cmd = CMD_CLOSE_MOD
                elif selected_speed == "1 Second - Slowest":
                    cmd = CMD_CLOSE_SLOW

                for v in GROUP_MAP[valve_name]:
                    self.changeValveStyle(v, "Closed")
                    self.comms.send_command(VALVE_ID_MAP[v], cmd)
                self.changeValveStyle(valve_name, "Closed")
            return

        # --- Single valve ---
        if button.text() == "Opened":
            if QMessageBox.question(self, "Confirm Action",
                    "Are you sure you want to close this valve?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) != QMessageBox.StandardButton.Yes:
                return

            is_solenoid = valve_name in ("SOV01F", "SOV02OX")

            if not is_solenoid and selected_speed == "Servo Closing Speed":
                QMessageBox.warning(self, "No Speed Selected", "Please select a servo closing speed.")
                return

            if is_solenoid or selected_speed == "0.3 Seconds - Fastest":
                cmd = CMD_CLOSE
            elif selected_speed == "0.6 Seconds - (Recommended) Moderate":
                cmd = CMD_CLOSE_MOD
            elif selected_speed == "1 Second - Slowest":
                cmd = CMD_CLOSE_SLOW

            self.changeValveStyle(valve_name, "Closed")
            self.comms.send_command(VALVE_ID_MAP[valve_name], cmd)

        elif button.text() == "Closed":
            if QMessageBox.question(self, "Confirm Action",
                    "Are you sure you want to open this valve?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) != QMessageBox.StandardButton.Yes:
                return

            self.changeValveStyle(valve_name, "Opened")
            self.comms.send_command(VALVE_ID_MAP[valve_name], CMD_OPEN)

    def blowdown_tick(self):
        """Called every 100ms by blowdown_timer — never blocks the UI."""
        if not self.blowdown_active:
            self.blowdown_timer.stop()
            return

        # Phase 1: wait for pressure to drop before closing N2 valves
        pt01 = self.graph_data["PT01F"][-1] if self.graph_data["PT01F"] else 999
        pt04 = self.graph_data["PT04F"][-1] if self.graph_data["PT04F"] else 999

        if pt01 > 900 or pt04 > 900:
            self.comms.send_command(0, CMD_CLOSE_MOD)
            self.comms.send_command(3, CMD_CLOSE_MOD)
            return  # come back next tick, not done yet

        # Phase 2: pressure is low — now watch LC for stability
        lc_val = self.graph_data["LC01F"][-1] if self.graph_data["LC01F"] else None

        if lc_val is None:
            return

        if self.lc_last_value is None:
            self.lc_last_value = lc_val
            return

        if abs(lc_val - self.lc_last_value) < 100:
            self.lc_stable_count += 1
        else:
            self.lc_stable_count = 0  # reset if it jumps again

        self.lc_last_value = lc_val

        # 10 consecutive stable readings at 100ms each = 1 stable second
        if self.lc_stable_count >= 10:
            self.blowdown_active = False
            self.blowdown_timer.stop()
            self.checklist["Blowdown"].setChecked(True)
            self.comms.send_command(0, CMD_CLOSE)
            self.comms.send_command(3, CMD_CLOSE)
            QMessageBox.information(self, "Blowdown Complete", "Load cell stable. Blowdown finished.")


    def closeEvent(self, event):
        self.plot_timer.stop()
        self.comms.stop()
        self.comms.wait()
        event.accept()
           

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())