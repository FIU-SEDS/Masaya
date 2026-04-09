import socket
import csv
import os
import time
import struct
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal


# ─────────────────────────────────────────────
#  Protocol Constants
# ─────────────────────────────────────────────

TELEM_LEN    = 28
TELEM_HEADER = 0xFF

# Device IDs
SEV01F = 0
SEV02F = 1
SEV03OX = 2
SEV04OX = 3
SOV01F = 4
SOV02OX = 5

# Commands
CMD_OPEN = 0x01
CMD_CLOSE_MOD  = 0x02
CMD_CLOSE_SLOW = 0x03
CMD_CLOSE     = 0x04

# Sensor names in order they appear in the telemetry frame
SENSOR_NAMES = [
    "PT0", "PT1", "PT2", "PT3",   # ADS1115 #1
    "PT4", "PT5", "PT6", "PT7",   # ADS1115 #2
    "TC0", "TC1", "TC2",          # ADS1115 #3
    "LC0", "LC1",                 # HX711s
]

CSV_HEADER = ["timestamp"] + SENSOR_NAMES


# ─────────────────────────────────────────────
#  Telemetry Parser
# ─────────────────────────────────────────────

def parse_telemetry(data: bytes) -> dict | None:
    """
    Parse a 28-byte telemetry frame from the STM32.

    Frame format:
        [0xFF] [sensor0_H] [sensor0_L] ... [sensor12_H] [sensor12_L] [XOR checksum]

    Each sensor is a uint16 = actual_value * 10  (1 decimal place precision)

    Returns a dict of {sensor_name: float} or None if invalid.
    """
    if len(data) != TELEM_LEN:
        return None
    if data[0] != TELEM_HEADER:
        return None

    # XOR checksum over all bytes except the last
    checksum = 0
    for b in data[:-1]:
        checksum ^= b
    if checksum != data[-1]:
        return None

    readings = {}
    for i, name in enumerate(SENSOR_NAMES):
        offset = 1 + i * 2
        raw = (data[offset] << 8) | data[offset + 1]
        readings[name] = raw / 10.0

    return readings


# ─────────────────────────────────────────────
#  Command Builder
# ─────────────────────────────────────────────

def build_command(device_id: int, cmd: int) -> bytes:
    """
    Build a 3-byte command frame.

    Frame format:
        [DEVICE_ID] [CMD] [XOR checksum]
    """
    checksum = device_id ^ cmd
    return bytes([device_id, cmd, checksum])


# ─────────────────────────────────────────────
#  DAQ Communications Thread
# ─────────────────────────────────────────────

class DAQComms(QThread):
    """
    Handles all UDP communication with the STM32 via CH9121 ethernet module.

    - Receives telemetry at ~50ms intervals and emits parsed sensor data
    - Logs all telemetry to a timestamped CSV file
    - Exposes send_command() for controlling valves and solenoids

    Signals:
        telemetry_received(dict)  — emitted on every valid telemetry frame
        connection_lost()         — emitted if no data received for timeout_s seconds
        connection_restored()     — emitted when data resumes after a loss
        log_error(str)            — emitted on CSV write errors
    """

    telemetry_received = pyqtSignal(dict)
    connection_lost    = pyqtSignal()
    connection_restored = pyqtSignal()
    log_error          = pyqtSignal(str)

    def __init__(
        self,
        stm32_ip:   str = "192.168.1.200",
        stm32_port: int = 2000,
        listen_ip:  str = "0.0.0.0",
        listen_port: int = 5005,
        timeout_s:  float = 2.0,
        csv_dir:    str = "logs",
    ):
        super().__init__()

        self.stm32_ip    = stm32_ip
        self.stm32_port  = stm32_port
        self.listen_ip   = listen_ip
        self.listen_port = listen_port
        self.timeout_s   = timeout_s
        self.csv_dir     = csv_dir

        self._running    = False
        self._sock       = None
        self._csv_file   = None
        self._csv_writer = None
        self._connected  = True  # optimistic start; flip on first timeout

    # ── Public API ────────────────────────────

    def send_command(self, device_id: int, cmd: int) -> None:
        """
        Send a valve/solenoid command to the STM32.
        Safe to call from any thread.

        Example:
            comms.send_command(SERVO_0, CMD_OPEN)
            comms.send_command(SOLENOID_1, CMD_CLOSE)
        """
        if self._sock is None:
            return
        frame = build_command(device_id, cmd)
        try:
            self._sock.sendto(frame, (self.stm32_ip, self.stm32_port))
        except OSError as e:
            print(f"[DAQComms] Send error: {e}")

    def stop(self) -> None:
        """Gracefully stop the thread."""
        self._running = False

    # ── Internal ──────────────────────────────

    def run(self):
        self._running = True
        self._open_csv()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(self.timeout_s)

        try:
            self._sock.bind((self.listen_ip, self.listen_port))
            print(f"[DAQComms] Listening on {self.listen_ip}:{self.listen_port}")
        except OSError as e:
            print(f"[DAQComms] Bind failed: {e}")
            return

        last_rx = time.monotonic()

        while self._running:
            try:
                data, _ = self._sock.recvfrom(1024)
                last_rx = time.monotonic()

                # Restore connection state if it was lost
                if not self._connected:
                    self._connected = True
                    self.connection_restored.emit()

                parsed = parse_telemetry(data)
                if parsed:
                    self.telemetry_received.emit(parsed)
                    self._log_row(parsed)

            except socket.timeout:
                if time.monotonic() - last_rx > self.timeout_s and self._connected:
                    self._connected = False
                    self.connection_lost.emit()

            except OSError as e:
                if self._running:
                    print(f"[DAQComms] Socket error: {e}")
                break

        self._cleanup()

    def _open_csv(self) -> None:
        os.makedirs(self.csv_dir, exist_ok=True)
        filename = datetime.now().strftime("daq_%Y%m%d_%H%M%S.csv")
        filepath = os.path.join(self.csv_dir, filename)
        try:
            self._csv_file   = open(filepath, "w", newline="")
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=CSV_HEADER)
            self._csv_writer.writeheader()
            self._csv_file.flush()
            print(f"[DAQComms] Logging to {filepath}")
        except OSError as e:
            self.log_error.emit(f"Could not open CSV: {e}")

    def _log_row(self, readings: dict) -> None:
        if self._csv_writer is None:
            return
        try:
            row = {"timestamp": datetime.now().isoformat(timespec="milliseconds")}
            row.update(readings)
            self._csv_writer.writerow(row)
            self._csv_file.flush()  # flush every row so data isn't lost on crash
        except OSError as e:
            self.log_error.emit(f"CSV write error: {e}")

    def _cleanup(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
        print("[DAQComms] Stopped.")