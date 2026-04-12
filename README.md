# Masaya Ground Station Dashboard

Real-time data acquisition and valve control interface for the Masaya liquid rocket engine test stand. Built with Python and PyQt6, communicating with an STM32 microcontroller over UDP via a CH9121 Ethernet module.

---

## Overview

The ground station provides:
- Live telemetry display at 100Hz from 8 pressure transducers, 3 thermocouples, and 2 load cells
- Valve control for 4 servo valves and 2 solenoid valves
- Mass flow rate (MFR) estimation via linear regression on load cell data
- Leak test sequencing (localized at 10 PSI, total at 900 PSI) with automated solenoid burping
- Automated blowdown sequence with load cell stability detection
- Real-time scrolling charts (30s window, 20Hz redraw) across organized tabs
- Timestamped CSV logging of all telemetry to `logs/`

---

## System Architecture

```
STM32 (Firmware)
    │
    │  UART 115200 baud
    ▼
CH9121 Ethernet Module
    │
    │  UDP  192.168.1.200:2000  (TX to STM32)
    │  UDP  0.0.0.0:5005        (RX telemetry)
    ▼
Ground Station PC
├── MasayaBack.py   — DAQ comms thread, telemetry parser, CSV logger
└── MasayaControl.py — PyQt6 GUI, charts, valve controls
```

### Telemetry Frame (STM32 → PC)
40-byte UDP frame at 10ms intervals:

| Byte | Content |
|------|---------|
| 0 | Header `0xFF` |
| 1–16 | PT0–PT7 (8× uint16, value × 10) |
| 17–22 | TC0–TC2 (3× uint16, value × 10) |
| 23–26 | LC0–LC1 (2× uint16, value × 10) |
| 27–34 | SEV01F–SEV04OX positions (4× uint16) |
| 35–38 | SOV01F–SOV02OX positions (2× uint16) |
| 39 | XOR checksum |

### Command Frame (PC → STM32)
3-byte UDP frame:

| Byte | Content |
|------|---------|
| 0 | Device ID |
| 1 | Command |
| 2 | XOR checksum |

**Device IDs:** SEV01F=0, SEV02F=1, SEV03OX=2, SEV04OX=3, SOV01F=4, SOV02OX=5

**Commands:** OPEN=0x01, CLOSE_MOD=0x02, CLOSE_SLOW=0x03, CLOSE=0x04, LLT=0x06, TLT=0x07

---

## Sensor Mapping

| UI Label | Telemetry Key | Physical Sensor |
|----------|--------------|-----------------|
| PT01F | PT0 | ADS1115 #1 CH0 |
| PT02F | PT1 | ADS1115 #1 CH1 |
| PT04F | PT2 | ADS1115 #1 CH2 |
| PT03F | PT3 | ADS1115 #1 CH3 |
| PT06OX | PT4 | ADS1115 #2 CH0 |
| PT07OX | PT5 | ADS1115 #2 CH1 |
| PT08OX | PT6 | ADS1115 #2 CH2 |
| PT09OX | PT7 | ADS1115 #2 CH3 |
| TC01F | TC0 | ADS1115 #3 CH0 |
| TC02OX | TC1 | ADS1115 #3 CH1 |
| TC02F | TC2 | ADS1115 #3 CH2 |
| LC01F | LC0 | HX711 #1 (IPA tank) |
| LC02OX | LC1 | HX711 #2 (N2O tank) |

**Leak test PT monitoring:**
- SOV-01-F burps when PT-02-F (PT1) exceeds threshold
- SOV-02-OX burps when PT-08-OX (PT6) exceeds threshold

---

## Requirements

**Python 3.10+**

```
PyQt6
PyQt6-Qt6
PyQt6-sip
PyQt6-WebEngine (optional)
pyqtgraph
numpy
pyqtgraph
```

Install dependencies:
```bash
pip install PyQt6 pyqtgraph numpy
```

**Assets:**

Place the PID schematic image at:
```
assets/final_PID.png
```

---

## Running

```bash
python MasayaControl.py
```

Ensure your machine is on the same subnet as the CH9121 (`192.168.1.x`). The DAQ thread binds to `0.0.0.0:5005` and sends commands to `192.168.1.200:2000`.

---

## Network Configuration

| Parameter | Value |
|-----------|-------|
| STM32/CH9121 IP | `192.168.1.200` |
| STM32 RX port | `2000` |
| Ground station listen port | `5005` |
| Protocol | UDP |

If your network adapter IP is not in the `192.168.1.x` range, either set a static IP on your adapter or adjust the addresses in `MasayaControl.py` where `DAQComms` is instantiated.

---

## Tab Layout

| Tab | Contents |
|-----|----------|
| Main/Schem | PID schematic overlay with live sensor labels and valve buttons |
| N2 Lines | TC01F, TC03OX, PT01F, PT09OX charts |
| N2O Lines | TC02OX, PT06OX, PT07OX, PT08OX charts |
| IPA Lines | TC02F, PT02F, PT04F charts |
| LC/Thrust | LC01F, LC02OX, PT03F charts |
| PT Sensors | All PT sensors duplicated for reference |

---

## Test Sequence (GO Button)

The GO button walks through a mandatory checklist in order. Each step must be completed before the next is available:

1. **Total Leak Test** — Sends LLT/TLT command to both solenoids. Solenoids burp at 100ms intervals while their associated PT reads above threshold. Press STOP to end.
2. **Localized Leak Test** — Same as above at 10 PSI threshold.
3. **Press Tanks** — Opens SEV01F and SEV04OX (upstream servo valves).
4. **Blowdown** — Opens SEV02F and SEV03OX (downstream). Monitors PT01F and PT04F for pressure drop below 900 PSI, then watches LC01F for 1 second of stability before auto-closing all valves.

**STOP button** immediately closes all 6 valves regardless of state.

---

## CSV Logging

A new CSV file is created in `logs/` on every launch, named `daq_YYYYMMDD_HHMMSS.csv`. Every valid telemetry frame is written as a row with a millisecond-precision timestamp. The file is flushed on every row so data is preserved even on crash.

---

## File Structure

```
masaya-groundstation/
├── MasayaControl.py     # GUI — main window, charts, valve controls
├── MasayaBack.py        # DAQ comms thread, parser, CSV logger
├── assets/
│   └── final_PID.png    # PID schematic background image
└── logs/                # Auto-created, timestamped CSV telemetry logs
```

---

## Known Limitations

- Servo closing speed must be selected from the dropdown before issuing a close command — the UI will warn if none is selected
- MFR calculation requires at least 20 buffered load cell samples (~0.2s) before displaying
- The blowdown sequence monitors LC01F only for stability; LC02OX is not part of the stop condition
- Negative sensor readings (e.g. load cell tare drift, sub-ambient TC) are clipped to 0 in the firmware fixed-point encoding and will display as 0.0 on the dashboard
