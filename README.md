# 🏢 8051 Elevator Control System Simulator

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-gold.svg)
![Flask](https://img.shields.io/badge/Flask-SocketIO-black.svg)
![Render](https://img.shields.io/badge/Hosted_on-Render-purple.svg)

A high-fidelity, real-time elevator control system originally designed to interface with 8051 Assembly firmware via physical UART. It has been evolved into a robust, 16-floor full-stack simulation deployed on the web. 

This project bridges low-level embedded systems concepts (Finite State Machines, ISRs, UART communication) with modern web technologies to create a seamlessly integrated, industrial-grade elevator cabin UI.

---

## 🚀 Live Demo & Testing

You can interact with the live simulation online here:  
**🔗 [Elevator Control System (Hosted on Render)](https://elevatorcontrolsystem.onrender.com)**

### How to Test Online:
1. **Call the Elevator:** Click any lighted floor button (G through 15) on the right-side control panel. The button rim will glow orange to indicate the call is queued.
2. **Observe the State:** Watch the top digital indicator dynamically update the floor and travel direction (▲/▼).
3. **Analytics:** The right-hand "System Analytics" panel shows the real-time continuous vertical position of the cabin and the underlying backend serial metrics stream.
4. **Emergency:** Press the red **STOP (Emergency)** button at any time. The elevator software will force a halt, clear all queues, and immediately open the doors safely. 

---

## ✨ Key Features
* **16-Floor Navigation:** Full travel capabilities between Ground and the 15th floor with a dynamic, camera-following background viewport simulating vertical movement.
* **Smart LOOK Scheduling Algorithm:** Implements a realistic disk-scheduling style algorithm handling simultaneous multi-floor requests, direction pivoting, and continuous non-redundant sweeps.
* **Real-time WebSockets:** Bidirectional, low-latency communication using `Flask-SocketIO` to sync backend FSM ticks with frontend cabin UI rendering.
* **Dual Execution Modes:** 
  * *Hardware Mode:* Attempts to bridge directly with Keil μVision via simulated COM ports sending HEX buffers.
  * *Virtual Core Mode (Cloud):* Falls back to a deterministic Python-based 8051 FSM emulator when deployed to cloud servers like Render.

---

## 🧠 Technical Architecture

### 1. The Presentation Layer (Frontend)
Built using standard **HTML / CSS / Vanilla JavaScript**. It strictly acts as a "dumb terminal" — it makes zero logic decisions. It purely displays the state handed to it by the backend WebSockets (`io()`) and sends back button-press events.
* Advanced CSS methodologies are utilized to give it a photorealistic, brushed-metal feeling with micro-interactions and incandescent LED glows.

### 2. The Bridge Layer (Backend)
Built with **Python, Flask, and Gunicorn**.
* Utilizes asynchronous Eventlet workers to manage infinite hardware loops without blocking standard web traffic.
* Manages the global `serial_reader_thread` tracking continuous hardware state.

### 3. The Logic Core (8051 Emulator)
If hardware serial is absent (like on Render), the backend implements a strict `Core8051Simulator` class.
* Emulates states: `IDLE`, `MOVING`, `SETTLING`, `DOOR_OPEN`, `DOOR_CLOSING`.
* Emulates exact `Interrupts` and `TARGET_MASK` bitwise operations as originally implemented in the `.asm` codebase.

---

## ⚙️ The LOOK Elevator Algorithm
Instead of blindly serving requests (First-Come First-Serve), the backend determines the optimal travel path using the **LOOK Algorithm**:
1. When moving `UP`, the elevator will continue satisfying all requested floors above it.
2. It stops strictly at the highest requested floor, reversing direction `DOWN` if and only if there are queued requests below it.
3. This prevents "starvation" of users at extreme ends of the building while minimizing travel distance. 

---

## 🛠️ Local Development

### Prerequisites
* Python 3.10+
* If you intend to use the actual 8051 code: Keil μVision and a Virtual Serial Port.

### Setup
1. Clone this repository to your local machine.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the development server:
   ```bash
   python server.py
   ```
5. Navigate to `http://localhost:5000` in your web browser.

---

## ☁️ Deployment (Render)
This repository is configured out-of-the-box for **Render.com** Platform-as-a-Service using the included `render.yaml` Blueprint and `Procfile`.
* **Runtime:** Python 3.11.8
* **Web Server:** Gunicorn with `eventlet` async workers.
* **Environment:** To deploy, simply link your GitHub to Render and it will auto-detect the provided build parameters.
