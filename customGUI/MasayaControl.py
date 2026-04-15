import sys, os, socket, time, MasayaBack
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QCheckBox, QDialog, QMessageBox, QVBoxLayout, QWidget, QTabWidget, QComboBox, QGridLayout, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from MasayaBack import DAQComms, CMD_OPEN, CMD_CLOSE_MOD, CMD_CLOSE_SLOW, CMD_CLOSE, CMD_LLT, CMD_TLT
from collections import deque
import pyqtgraph as pg
import numpy as np
from PyQt6.QtSvgWidgets import QSvgWidget



class DiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.blowdown_active = False
        self.lc_stable_count = 0
        self.lc_last_value   = None
        self.blowdown_timer  = QTimer()
        self.blowdown_timer.timeout.connect(self.blowdown_tick)
        self.blowdown_timer.setInterval(100)

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

        # Main Page top left
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
            ("Conduct total leak test"), ("Conduct localized leak test"), ("Press Tanks"), ("Blowdown")
        ]
        self.checklist = {}
        for name in checklist_steps:
            chk = QCheckBox(name)
            chk.setStyleSheet(checklist_style)
            self.topLeft.addWidget(chk)
            self.checklist[name] = chk

        self.topLeftContainer = QWidget(self.tab1)
        self.topLeftContainer.setLayout(self.topLeft)
        self.topLeftContainer.move(18, 10)
        self.topLeftContainer.adjustSize()

        # Main Page top right (Status)
        self.statusTitle = QLabel("Status", self.tab1)
        self.statusTitle.setStyleSheet("color: white; font-size: 25px; font-weight: bold;")
        self.statusTitle.adjustSize()

        status_style = "font-family: 'Consolas'; color: white; font-size: 20px; font-weight: bold;"
        self.status = QLabel('<span style="color: red; font-size: 20pt;">●</span> DAQ Not Found', self.tab1)
        self.status.setStyleSheet(status_style)
        self.status.adjustSize()

        self.topRight = QVBoxLayout()
        self.topRight.addWidget(self.statusTitle)
        self.topRight.addWidget(self.status)
        self.topRightContainer = QWidget(self.tab1)
        self.topRightContainer.setLayout(self.topRight)
        self.topRightContainer.move(1250, 10)
        self.topRightContainer.adjustSize()

        # GO / STOP Buttons
        self.START = QPushButton("GO", self.tab1)
        self.START.move(18, 758)
        self.START.resize(267, 44)
        self.START.setStyleSheet("""
            QPushButton { color: white; font-size: 18px; font-weight: bold; background-color: green; }
            QPushButton:pressed { background-color: darkgreen; }
        """)
        self.START.clicked.connect(self.GO)

        self.STOP = QPushButton("STOP", self.tab1)
        self.STOP.move(18, 811)
        self.STOP.resize(267, 71)
        self.STOP.setStyleSheet("""
            QPushButton { color: white; font-size: 18px; font-weight: bold; background-color: red; }
            QPushButton:pressed { background-color: darkred; }
        """)
        self.STOP.clicked.connect(self.STOP_Test)

        # Last minute Fixed to UI background to match current setup
        self.movedTCLabelBack  = self._make_cover(920, 735, 140, 28, "red")
        self.movedTCLabelFront = self._make_cover(923, 738, 95, 22)
        self.movedTCLabel      = self._make_label("PT-03-F", 957, 700)
        self.movedTCLabelPSIG  = self._make_label("psig", 1025, 735, size=17)

        self.PTCOVER  = self._make_cover(1410, 490, 180, 100)
        self.PTCOVER2 = self._make_cover(1410, 476, 50, 50)
        self.PTCOVER3 = self._make_cover(970, 260, 100, 25)
        self.PTCOVER4 = self._make_cover(970, 30, 100, 25)
        self.PTCOVER5 = self._make_cover(940, 580, 130, 110)
        self.LCCOVER  = self._make_cover(600, 390, 150, 180)

        self.movedTCLabel1 = self._make_label("TC-02-OX", 970, 260)
        self.movedTCLabel2 = self._make_label("TC-03-OX", 975, 30)

        self.redline = self._make_cover(920, 620, 150, 2, "red")

        self.waterWeightCover  = self._make_cover(765, 238, 115, 25)
        self.waterWeightCover1 = self._make_cover(765, 549, 115, 25)

        self.movedLCLabel1 = self._make_label("LC-02-OX", 785, 238)
        self.movedLCLabel2 = self._make_label("LC-01-F", 793, 549)

        # Valve Buttons
        valve_button_off = """
            QPushButton { color: black; font-size: 18px; font-weight: bold; background-color: gray; }
            QPushButton:pressed { background-color: gray; }
        """
        valve_configs = [
            ("SEV01F", 610, 650), ("SEV02F", 1085, 650),
            ("SEV03OX", 1085, 335), ("SEV04OX", 610, 335),
            ("SOV01F", 850, 853), ("SOV02OX", 850, 96),
            ("Downstream", 1085, 450), ("Upstream", 610, 450)
        ]
        self.valves = {}
        for name, x, y in valve_configs:
            but = QPushButton("Closed", self.tab1)
            but.move(x, y)
            but.setStyleSheet(valve_button_off)
            but.resize(100, 25)
            self.valves[name] = but
            but.clicked.connect(lambda checked=False, v_name=name: self.valveOC(v_name))


        # SVG Arrows
        self.arrows = QSvgWidget(self.tab1)
        self.arrows.load(b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="1580" height="900">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7"
                        refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="white"/>
                </marker>
            </defs>
            <line x1="660" y1="490" x2="660" y2="550" stroke="white" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="660" y1="430" x2="660" y2="380" stroke="white" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="1135" y1="430" x2="1135" y2="375" stroke="white" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="1135" y1="500" x2="1135" y2="555" stroke="white" stroke-width="2" marker-end="url(#arrowhead)"/>
        </svg>
        """)
        self.arrows.setGeometry(0, 0, 1580, 900)
        self.arrows.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.arrows.raise_()        
        

        # Schematic Labels
        sensor_label_style = "color: white; font-size: 20px; font-weight: bold;"
        sensor_configs = [
            ("LC01F", 780, 579), ("LC02OX", 780, 268),
            ("TC01F", 970, 820), ("TC03OX", 970, 60), ("TC02OX", 962, 290),
            ("PT01F", 450, 607), ("PT02F", 630, 752), ("PT04F", 1240, 607),
            ("PT03F", 926, 732), ("PT06OX", 1240, 290), ("PT07OX", 890, 147), ("PT08OX", 630, 147),
            ("PT09OX", 450, 290),
            ("MFR_n2o", 773, 332), ("MFR_ipa", 773, 650)
        ]
        self.sensors = {}
        for name, x, y in sensor_configs:
            lbl = QLabel("-----", self.tab1)
            lbl.move(x, y)
            lbl.setStyleSheet(sensor_label_style)
            lbl.setFixedWidth(80)
            lbl.raise_()
            self.sensors[name] = lbl
        
    
        # ── Charts ────────────────────────────────────────────────────────────
        self.n2Charts    = QGridLayout(self.tab2)
        self.n2oCharts   = QGridLayout(self.tab3)
        self.ipaCharts   = QGridLayout(self.tab4)
        self.otherCharts = QGridLayout(self.tab5)
        self.ptSensors   = QGridLayout(self.tab6)

        sensor_configs_graphs = [
            ("LC01F", self.otherCharts, 0, 0), ("LC02OX", self.otherCharts, 0, 1),
            ("TC01F", self.n2Charts, 1, 0), ("TC03OX", self.n2Charts, 0, 0), ("TC02OX", self.n2oCharts, 1, 0), ("TC02F", self.ipaCharts, 1, 0),
            ("PT01F", self.n2Charts, 1, 1), ("PT02F", self.ipaCharts, 0, 0), ("PT04F", self.ipaCharts, 1, 1),
            ("PT03F", self.otherCharts, 0, 2), ("PT06OX", self.n2oCharts, 1, 1), ("PT07OX", self.n2oCharts, 0, 1), ("PT08OX", self.n2oCharts, 0, 0),
            ("PT09OX", self.n2Charts, 0, 1)
        ]

        self.sensorsGraphs   = {}
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
        HISTORY_S  = 30
        MAX_POINTS = HISTORY_S * 100

        self.t_start     = time.monotonic()
        self.graph_times = deque(maxlen=MAX_POINTS)

        graph_sensor_names = [
            "LC01F", "LC02OX",
            "TC01F", "TC03OX", "TC02OX", "TC02F",
            "PT01F", "PT02F", "PT04F", "PT03F",
            "PT06OX", "PT07OX", "PT08OX", "PT09OX",
        ]
        self.graph_data = {name: deque(maxlen=MAX_POINTS) for name in graph_sensor_names}

        self.graph_key_map = {
            "PT01F": "PT0", "PT02F": "PT1", "PT04F": "PT2", "PT03F": "PT3",
            "PT06OX": "PT4", "PT07OX": "PT5", "PT08OX": "PT6", "PT09OX": "PT7",
            "LC01F": "LC0", "LC02OX": "LC1",
            "TC01F": "TC0", "TC02OX": "TC1", "TC03OX": "TC2",
        }

        # Pre-create curves and value lines for every chart
        self.graph_curves    = {}
        self.graph_curves_pt = {}
        self.value_lines     = {}   # main tab dashed lines
        self.value_lines_pt  = {}   # PT duplicate tab dashed lines

        dashed_pen = pg.mkPen('w', width=1, style=Qt.PenStyle.DashLine)

        for name in graph_sensor_names:
            if name in self.sensorsGraphs:
                self.graph_curves[name] = self.sensorsGraphs[name].plot(
                    pen=pg.mkPen('y', width=2)
                )
                vline = pg.InfiniteLine(angle=0, movable=False, pen=dashed_pen)
                pg.InfLineLabel(
                    vline, text="{value:.1f}", position=0.95,
                    color='w', fill=pg.mkBrush(0, 0, 0, 150)
                )
                self.sensorsGraphs[name].addItem(vline)
                self.value_lines[name] = vline

            if name in self.ptSensorsGraphs:
                self.graph_curves_pt[name] = self.ptSensorsGraphs[name].plot(
                    pen=pg.mkPen('c', width=2)
                )
                vline_pt = pg.InfiniteLine(angle=0, movable=False, pen=dashed_pen)
                pg.InfLineLabel(
                    vline_pt, text="{value:.1f}", position=0.95,
                    color='w', fill=pg.mkBrush(0, 0, 0, 150)
                )
                self.ptSensorsGraphs[name].addItem(vline_pt)
                self.value_lines_pt[name] = vline_pt

        # Redraw timer — 20Hz
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
        # 1. Sensor label map
        sensor_map = {
            "PT01F": "PT0", "PT02F": "PT1", "PT04F": "PT2", "PT03F": "PT3",
            "PT06OX": "PT4", "PT07OX": "PT5", "PT08OX": "PT6", "PT09OX": "PT7",
            "LC01F": "LC0", "LC02OX": "LC1",
            "TC01F": "TC0", "TC02OX": "TC1", "TC03OX": "TC2"
        }

        # 2. Update schematic text labels
        for ui_key, data_key in sensor_map.items():
            if data_key in data:
                self.sensors[ui_key].setText(f"{data[data_key]:.1f}")

        # 3. Update valve button styles
        valves = ['SEV01F', 'SEV02F', 'SEV03OX', 'SEV04OX', 'SOV01F', 'SOV02OX']
        for valve in valves:
            status = "Opened" if data.get(valve) == 90 else "Closed"
            self.changeValveStyle(valve, status)

        # 4. Buffer graph data — no drawing here
        t = time.monotonic() - self.t_start
        self.graph_times.append(t)
        for ui_name, data_key in self.graph_key_map.items():
            if data_key in data:
                self.graph_data[ui_name].append(data[data_key])

        # 5. MFR via best-fit slope on LC
        t_list = list(self.graph_times)

        for ui_key, lc_key in [("MFR_ipa", "LC01F"), ("MFR_n2o", "LC02OX")]:
            lc_list = list(self.graph_data[lc_key])
            if len(lc_list) >= 20 and len(t_list) >= 20:
                y      = np.array(lc_list[-20:])
                t_arr  = np.array(t_list[-20:])
                coeffs = np.polyfit(t_arr, y, 1)
                mfr    = abs(coeffs[0])  # kg/s, take abs so display is positive
                self.sensors[ui_key].setText(f"{mfr:.2f}")


    def update_graphs(self):
        """Called every 50ms (20Hz). Updates curves and value lines for all charts."""
        if not self.graph_times:
            return

        t     = list(self.graph_times)
        x_min = t[-1] - 30  # show last 30 seconds

        # Main tab charts
        for name, curve in self.graph_curves.items():
            y = list(self.graph_data[name])
            if not y:
                continue
            t_trimmed = t[-len(y):]
            curve.setData(t_trimmed, y)
            self.sensorsGraphs[name].setXRange(x_min, t[-1], padding=0)
            if name in self.value_lines:
                self.value_lines[name].setValue(y[-1])

        # PT duplicate charts in tab6
        for name, curve in self.graph_curves_pt.items():
            y = list(self.graph_data[name])
            if not y:
                continue
            t_trimmed = t[-len(y):]
            curve.setData(t_trimmed, y)
            self.ptSensorsGraphs[name].setXRange(x_min, t[-1], padding=0)
            if name in self.value_lines_pt:
                self.value_lines_pt[name].setValue(y[-1])


    def GO(self):
        total_leak = self.checklist["Conduct total leak test"].isChecked()
        local_leak = self.checklist["Conduct localized leak test"].isChecked()
        press_tank = self.checklist["Press Tanks"].isChecked()
        blowdown   = self.checklist["Blowdown"].isChecked()

        if total_leak and local_leak and blowdown and press_tank:
            QMessageBox.information(self, "Success", "All tests completed. System ready.")
            return

        if not total_leak:
            reply = QMessageBox.question(
                self, "Warning",
                "Do you want to conduct a total leak test?\n\nNote: Activates Burping for 900 psig on the following valves and PTs:\n"
                "SOV-01-F\t--\tPT-02-F\nSOV-02-OX\t--\tPT-08-OX\nPress STOP to stop test.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.comms.send_command(4, CMD_TLT)

        elif not local_leak:
            reply = QMessageBox.question(
                self, "Warning",
                "Do you want to conduct a local leak test?\n\nNote: Activates Burping for 10 psig on the following valves and PTs:\n"
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
                self.blowdown_active = True
                self.lc_stable_count = 0
                self.lc_last_value   = None
                self.blowdown_timer.start()

    # Close all valves. Emergency stop/stop test.
    def STOP_Test(self):
        self.comms.send_command(4, CMD_CLOSE)
        self.comms.send_command(5, CMD_CLOSE)
        self.comms.send_command(0, CMD_CLOSE)
        self.comms.send_command(1, CMD_CLOSE)
        self.comms.send_command(2, CMD_CLOSE)
        self.comms.send_command(3, CMD_CLOSE)


    def changeValveStyle(self, valve_name, style):
        valve_button_off = """
            QPushButton { color: black; font-size: 18px; font-weight: bold; background-color: gray; }
            QPushButton:pressed { background-color: darkred; }
        """
        valve_button_on = """
            QPushButton { color: black; font-size: 18px; font-weight: bold; background-color: white; }
            QPushButton:pressed { background-color: darkgreen; }
        """
        button = self.valves[valve_name]
        if style == "Opened":
            button.setText("Opened")
            button.setStyleSheet(valve_button_on)
        else:
            button.setText("Closed")
            button.setStyleSheet(valve_button_off)

    # Valve Open/Close Logic
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

    # Logic for Blowndown
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
            return

        # Phase 2: pressure low — watch LC for stability
        lc_val = self.graph_data["LC01F"][-1] if self.graph_data["LC01F"] else None
        if lc_val is None:
            return

        if self.lc_last_value is None:
            self.lc_last_value = lc_val
            return

        if abs(lc_val - self.lc_last_value) < 100:
            self.lc_stable_count += 1
        else:
            self.lc_stable_count = 0

        self.lc_last_value = lc_val

        # 10 stable readings at 100ms = 1 stable second
        if self.lc_stable_count >= 10:
            self.blowdown_active = False
            self.blowdown_timer.stop()
            self.checklist["Blowdown"].setChecked(True)
            self.comms.send_command(0, CMD_CLOSE)
            self.comms.send_command(3, CMD_CLOSE)
            QMessageBox.information(self, "Blowdown Complete", "Load cell stable. Blowdown finished.")


    def _make_cover(self, x, y, width, height, color="black"):
        widget = QWidget(self.tab1)
        widget.setGeometry(x, y, width, height)
        widget.setStyleSheet(f"background-color: {color};")
        return widget
    
    def _make_label(self, text, x, y, color="white", size=18):
        lbl = QLabel(text, self.tab1)
        lbl.move(x, y)
        lbl.setStyleSheet(f"color: {color}; font-size: {size}px;")
        return lbl

    def closeEvent(self, event):
        self.plot_timer.stop()
        self.blowdown_timer.stop()
        self.comms.stop()
        self.comms.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramWindow()
    window.show()
    sys.exit(app.exec())