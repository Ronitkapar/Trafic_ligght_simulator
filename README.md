# Raspberry Pi Traffic Light Controller — Software Simulation

A software-only simulation of a Raspberry Pi-based traffic light controller. This project models the traffic signal timing sequence, control states, and hardware-level GPIO logic without requiring physical Raspberry Pi hardware, breadboards, LEDs, or resistors.

The project provides two simulation interfaces:
1. **Desktop GUI Application (`traffic_light_simulation.py`)**: Built with Python 3 and Tkinter using only Python's standard library.
2. **3D Interactive Web Application (`traffic_light_3d_simulation.html`)**: A photorealistic 3D workbench built with Three.js (WebGL) featuring an interactive Raspberry Pi 4 Model B, 40-pin GPIO header, breadboard-style jumper wires, terminal block with resistors, and customizable traffic signal housing.

---

## Traffic Light Sequence & Timing

Both simulations follow the standard single-lane repeating sequence:

| Step | Signal | Message | Default Duration | Behavior |
|:----:|:------:|:-------:|:----------------:|:---------|
| 1 | **RED** | STOP | 5 seconds | Red illuminated; stop traffic |
| 2 | **GREEN** | GO | 5 seconds | Green illuminated; proceed |
| 3 | **YELLOW** | GET READY | 2 seconds | Yellow illuminated; prepare to stop |
| 4 | **RED** | STOP | — | Cycle repeats back to Red |

* **Single-Light Invariant**: Strictly one light is illuminated at any given moment.
* **Non-blocking Timers**: Timing updates use event-loop callbacks (`root.after()` in Tkinter, non-blocking asynchronous timers in WebGL) rather than `time.sleep()`.

---

## Features

### 1. Desktop Simulation (`traffic_light_simulation.py`)
- **Zero Third-Party Dependencies**: Uses purely Python 3 standard library modules (`tkinter`, `ttk`).
- **Signal Housing**: Cast-aluminum housing graphic with circular lenses, active halo lighting, specular reflection accents, and an active countdown progress bar.
- **Responsive Controls**:
  - **Start**: Initiates or resumes the timed countdown without scheduling duplicate timers.
  - **Pause**: Halts the timer, preserves the active signal phase, and freezes the remaining countdown.
  - **Reset**: Stops the simulation, restores the initial RED state with its full duration, and resets the status badge to "Ready".
- **Clean Lifecycle & Resource Handling**: Cancels pending callbacks on pause, reset, or window closure (`WM_DELETE_WINDOW` and `<Destroy>`).
- **Configurable Durations**: Timings can be customized at the top of the script (`RED_SECONDS`, `GREEN_SECONDS`, `YELLOW_SECONDS`) with strict validation (positive integers only).

### 2. 3D WebGL Simulation (`traffic_light_3d_simulation.html`)
- **Interactive 3D Raspberry Pi 4 Model B**:
  - Detailed PCB model with Broadcom BCM2711 SoC, LPDDR4 RAM, USB controller, Ethernet and dual USB ports, USB-C, micro-HDMI, and onboard PWR/ACT LEDs.
  - Full **40-Pin GPIO Header (J8)** with hover tooltips showing pin numbers, BCM labels, logic levels, and voltages.
- **Dynamic 3D Jumper Wires**:
  - Procedurally generated 3D curved jumper wires with Dupont connectors routing from the Raspberry Pi pins across the workbench to the signal tower's screw terminals.
  - Luminous signal-flow pulse particles travelling down the active channel's wire.
- **Virtual GPIO Pin Mapping**:
  - Configure output pins for **RED** (default GPIO 17 / Pin 11), **YELLOW** (default GPIO 27 / Pin 13), and **GREEN** (default GPIO 22 / Pin 15), plus common Ground (Pin 6).
  - Selectable across any of the 17 usable BCM GPIO pins with automatic conflict resolution/swapping.
  - Interactive 2×20 mini GPIO header diagram showing live pin states (HIGH 3.3V / LOW 0.0V).
- **Customization Options**:
  - **Durations**: Live adjustment of Red, Green, and Yellow durations (1–60 seconds).
  - **Housing Finish**: Switch between *Cast Dark*, *Highway Yellow*, and *Brushed Silver*.
  - **Lens Glow Intensity**: Toggle between *Subtle*, *Standard*, and *Vivid*.
  - **Bench Lighting**: Switch between *Studio Daylight* and *Lab Night* modes.
  - **Camera Controls**: Orbit, pan, zoom, auto-orbit, and camera view presets (*Overview*, *Pi GPIO*, *Traffic Light*, *Top Wiring*).

### 3. Automated Test Suite (`test_traffic_light_simulation.py`)
- 15 comprehensive unit tests built with Python's `unittest` framework exercising real Tkinter widgets.
- Validates:
  - Timing constants, duration validators, and error rejection (`ValueError` on `<= 0`, non-int, bool, float, or None).
  - Complete two-cycle (24 ticks) state progression and single-active-light invariant.
  - Duplicate callback prevention, state preservation across pauses, and reset behavior.
  - Window closure cleanup, destroyed-widget resilience, and real `after()` timer execution.
  - Source verification confirming standard-library-only usage and absence of `sleep()`.

---

## Project Structure

```text
os_project/
├── README.md                                     # Project documentation
├── Raspberry_Pi_Traffic_Light_Simulation_Guide.md # Authoritative project specification
├── traffic_light_simulation.py                   # Desktop Tkinter simulation application
├── test_traffic_light_simulation.py              # Automated test suite for the Python simulation
└── traffic_light_3d_simulation.html              # Standalone 3D WebGL interactive simulation
```

---

## Getting Started

### Prerequisites

* **Python 3.10+** (tested on Python 3.14)
* **Tkinter** (usually included with standard Python installations; on Debian/Ubuntu install via `sudo apt install python3-tk`)
* A modern web browser with WebGL enabled (Chrome, Firefox, Edge, Safari) and internet access to load Three.js from the CDN.

---

### Running the Applications

#### 1. Desktop Tkinter Simulation

Run the Python application directly from the terminal:

```bash
python3 traffic_light_simulation.py
```

#### 2. Running Automated Tests

Run the test suite using Python's standard `unittest` runner:

```bash
python3 -m unittest -v test_traffic_light_simulation.py
```

#### 3. 3D WebGL Simulation

Start a local static HTTP server in the project directory:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open your browser and navigate to:

```text
http://127.0.0.1:8000/traffic_light_3d_simulation.html
```

---

## Default Virtual GPIO Pin Mapping

| Channel | Signal | BCM GPIO | Physical Header Pin | Default Voltage (Active) |
|:-------:|:------:|:--------:|:-------------------:|:------------------------:|
| 1 | **RED** | GPIO 17 | Pin 11 | 3.3V (HIGH) / 0.0V (LOW) |
| 2 | **YELLOW**| GPIO 27 | Pin 13 | 3.3V (HIGH) / 0.0V (LOW) |
| 3 | **GREEN** | GPIO 22 | Pin 15 | 3.3V (HIGH) / 0.0V (LOW) |
| — | **GND** | — | Pin 6 | 0.0V (Ground Return) |

*(Note: Virtual GPIO pins can be freely re-mapped in the 3D web application).*

---

## Scope Note

This software project is intended for educational and algorithmic simulation of traffic light logic, state machines, and embedded controller design. It does not execute physical Raspberry Pi kernel GPIO calls or interact with hardware circuits.
