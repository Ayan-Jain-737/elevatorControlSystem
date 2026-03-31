# 8051 Elevator Control System with Web UI

A 16-floor elevator control system using an 8051 microcontroller (P89V51RD2), a Python Serial bridge, and a modern Web Frontend.

## Architecture

1. **8051 Microcontroller (Core Logic)**
   - Executes the core FSM (IDLE, MOVING, DOOR_OPEN, EMERGENCY).
   - Handles the SCAN scheduling algorithm.
   - Parses UART commands (`CALL:1`, `EMERGENCY`).
   - Generates status updates (`F:2|D:U|DR:1|E:0\n`).

2. **Python Backend (Serial Bridge)**
   - Flask server with Flask-SocketIO.
   - Reads data from the 8051 via UART (pyserial).
   - Routes data bi-directionally between WebSockets and serial port.

3. **Web Frontend (UI)**
   - Modern, dynamic HTML/CSS/JS interface.
   - Real-time visualization of the elevator cabin and system parameters.

---

## Folder Structure

```text
mpmcElevatorProject/
│
├── elevator.asm          # 8051 Assembly source code (Keil)
├── server.py             # Python Flask + SocketIO bridge
├── requirements.txt      # Python dependencies
├── README.md             # Setup and run instructions
│
├── static/
│   ├── style.css         # Modern styling and animations
│   └── script.js         # WebSocket logic and UI updates
│
└── templates/
    └── index.html        # Main interface HTML
```

