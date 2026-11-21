# Raspberry Pi Traffic Light Controller
## Software Simulation Guide

## 1. Project objective

Create a **software simulation** of a traffic-light controller. The application displays a virtual traffic signal on the computer screen and changes its red, green, and yellow lights in a timed sequence.

This version does **not** use a physical Raspberry Pi, LEDs, resistors, breadboard, jumper wires, or GPIO connections. It models the traffic-light behaviour in a desktop window.

The sequence used in this example is:

1. **Red ON** for 5 seconds: Stop.
2. **Green ON** for 5 seconds: Go.
3. **Yellow ON** for 2 seconds: Prepare to stop.
4. Return to red and repeat.

Only one virtual light is illuminated at a time. The timings are examples because the supplied problem statement does not specify exact durations.

## 2. What we will use

- A computer running Windows, Linux, or macOS.
- Python 3.
- Tkinter, Python's standard GUI library. It is included with many Python installations.
- The supplied `traffic_light_simulation.py` program.

No third-party Python packages are required.

## 3. What the simulation will display

The application window contains:

- A virtual traffic-light housing with red, yellow, and green indicators.
- A status label showing the current signal and its meaning.
- A countdown showing the time remaining for the current signal.
- **Start**, **Pause**, and **Reset** controls.
- The configured duration of each signal.

## 4. Project files

Keep these two files in the same folder:

```text
traffic-light-simulation/
├── traffic_light_simulation.py
└── Raspberry_Pi_Traffic_Light_Simulation_Guide.md
```

The Python file contains the complete simulation. This Markdown file explains how to run and demonstrate it.

## 5. Check Python

Open Command Prompt or PowerShell on Windows, or a terminal on Linux/macOS. Run:

```bash
python --version
```

On some systems, use:

```bash
python3 --version
```

Python 3 is required. The simulation uses only Python's built-in modules.

### Check that Tkinter is available

On Windows, Tkinter is normally included with the standard Python installer. On Linux, install the Tkinter package if it is missing:

```bash
sudo apt update
sudo apt install python3-tk
```

You can check it with:

```bash
python -m tkinter
```

Use `python3 -m tkinter` if your system uses the `python3` command. A small test window should appear. Close it before continuing.

## 6. Run the simulation

Open a terminal in the folder containing `traffic_light_simulation.py` and run:

```bash
python traffic_light_simulation.py
```

On systems where the command is `python3`, run:

```bash
python3 traffic_light_simulation.py
```

A window containing the virtual traffic light should appear.

## 7. How to use the application

| Control | Behaviour |
|---|---|
| Start | Starts or resumes the timed sequence. |
| Pause | Pauses the countdown and keeps the current light displayed. |
| Reset | Stops the sequence and returns the display to red with its full duration. |
| Close window | Stops the timer and closes the simulation. |

When running, the application follows this cycle:

| Order | Virtual light | Meaning | Duration |
|---:|---|---|---:|
| 1 | Red | Stop | 5 seconds |
| 2 | Green | Go | 5 seconds |
| 3 | Yellow | Prepare to stop | 2 seconds |
| 4 | Red | Cycle repeats | 5 seconds |

## 8. Change the timings

At the top of `traffic_light_simulation.py`, update these constants:

```python
RED_SECONDS = 5
GREEN_SECONDS = 5
YELLOW_SECONDS = 2
```

For example, to use 10 seconds for red, 8 seconds for green, and 3 seconds for yellow:

```python
RED_SECONDS = 10
GREEN_SECONDS = 8
YELLOW_SECONDS = 3
```

All durations must be greater than zero. Restart the program after changing them.

## 9. How the program works

1. **Tkinter** creates the application window, virtual traffic-light drawing, labels, and buttons.
2. The three virtual indicators are drawn as circles on a canvas. Their colours change to show which signal is active.
3. `PHASES` stores the signal order, message, and duration.
4. The `Start` button begins the timer. The `Pause` button stops scheduling timer updates without changing the current signal.
5. Tkinter's `after()` method schedules the next update. It is used instead of `time.sleep()` so the window remains responsive while the simulation runs.
6. When a phase's countdown reaches zero, the program moves to the next phase. After yellow, it returns to red.
7. `Reset` returns the simulation to the initial red state.

## 10. Test checklist

- [ ] The application window opens successfully.
- [ ] Red is the first active light when the application starts.
- [ ] Pressing **Start** begins the countdown.
- [ ] Red remains active for the configured duration.
- [ ] Green becomes active after red.
- [ ] Yellow becomes active after green.
- [ ] The sequence returns to red and repeats.
- [ ] At most one light is active at a time.
- [ ] **Pause** freezes the current signal and countdown.
- [ ] **Start** resumes from the paused point.
- [ ] **Reset** returns to red and restores its full duration.
- [ ] Closing the window stops the timer cleanly.

## 11. Expected outcome

A working desktop-based traffic-light simulation that visibly demonstrates red, green, and yellow signal states, predefined timing, sequential execution, and a repeating control loop.

## 12. Demonstration explanation

> "Our project is a software simulation of a Raspberry Pi traffic-light controller. Instead of connecting physical LEDs to GPIO pins, we represent the three lights graphically on the computer screen. Python and Tkinter are used to display the signal and update it at fixed intervals. The program follows a red, green, and yellow sequence, repeats continuously, and provides Start, Pause, and Reset controls. This demonstrates the timing and sequential control logic without requiring a physical circuit."

## 13. Important scope note

The supplied problem statement mentions LEDs connected to Raspberry Pi GPIO pins, and its expected outcome mentions GPIO programming. This desktop version simulates the **traffic-light logic and visual output**, but it does not execute GPIO operations or verify Raspberry Pi hardware behaviour.

Use this version when the requirement is specifically to demonstrate a simulation without building a circuit. If an evaluator requires an actual Raspberry Pi GPIO simulator or evidence of GPIO API usage, confirm which simulator or environment they expect before claiming that this desktop application demonstrates GPIO programming.
