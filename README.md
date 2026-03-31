# 8051 Elevator Control System with Web UI

A 4-floor elevator control system using an 8051 microcontroller (P89V51RD2), a Python Serial bridge, and a modern Web Frontend.

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

---

## Step-by-Step Setup Instructions

### Part 1: Compiling the 8051 Code
1. Open **Keil µVision**.
2. Create a new project for target **NXP P89V51RD2** (or a generic 8051 derivative).
3. Add `elevator.asm` to the Source Group in the Project Workspace.
4. Go to **Options for Target** -> **Target** tab:
   - Set Xtal (MHz) to `11.0592`.
5. Under the **Output** tab:
   - Check `Create HEX File`.
6. Click **Rebuild** (F7).
7. Flash the resulting `.hex` file to your P89V51RD2 microcontroller or load it into a simulator (like Proteus).

### Part 2: Hardware Connections
- Connect the 8051 TX/RX pins to the PC using a USB-to-TTL UART adapter.
- Note the COM port assigned to the USB adapter (e.g., `COM3`, `COM4`).
- Modify the `SERIAL_PORT` variable in `server.py` to match your COM port (default is `COM1`, or use `set SERIAL_PORT=COM3` in your terminal).

### Part 3: Running the Python Server
1. Ensure Python 3.8+ is installed on your PC.
2. Open a terminal or Command Prompt in this directory (`d:\VIT Folders\MPMC\keil\mpmcElevatorProject`).
3. Create an optional virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the web server:
   ```bash
   python server.py
   ```

### Part 4: Accessing the UI
1. Open your web browser (Chrome, Edge, Firefox).
2. Navigate to [http://localhost:5000](http://localhost:5000).
3. The UI will establish a WebSocket connection to the Python backend.
4. Interact with the **Call floor** buttons to send commands across the stack down to the 8051. The status updates from the 8051 will actively manipulate the UI animations.
