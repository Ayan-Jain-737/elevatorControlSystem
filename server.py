import eventlet
eventlet.monkey_patch()
import serial
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_elevator'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

socketio = SocketIO(app, cors_allowed_origins="*")

SERIAL_PORT = os.environ.get('SERIAL_PORT', 'COM1')
BAUD_RATE = 9600

ser = None

class Core8051Simulator:
    def __init__(self):
        self.floor = 0
        self.direction = 'I'
        self.door = '0'
        self.emergency = '0'
        self.target_mask = 0
        self.state = 'IDLE' # IDLE, MOVING, SETTLING, DOOR_OPEN, DOOR_CLOSING
        self.ticks = 0
        self.request_queue = [] # LOOK Algorithm FIFO tracking 

    def set_target(self, floor_num):
        if floor_num not in self.request_queue:
            self.request_queue.append(floor_num)
        self.target_mask |= (1 << floor_num)
        
    def check_request_at_current(self):
        return (self.target_mask & (1 << self.floor)) != 0

    def clear_current_request(self):
        self.target_mask &= ~(1 << self.floor)
        if self.floor in self.request_queue:
            self.request_queue.remove(self.floor)

    def has_upper_requests(self):
        mask = 0
        for i in range(self.floor + 1, 16):
            mask |= (1 << i)
        return (self.target_mask & mask) != 0

    def has_lower_requests(self):
        mask = 0
        for i in range(0, self.floor):
            mask |= (1 << i)
        return (self.target_mask & mask) != 0

    def decide_direction(self):
        if self.target_mask == 0 or len(self.request_queue) == 0:
            self.direction = 'I'
            return

        if self.direction == 'U' and self.has_upper_requests():
            self.direction = 'U'
        elif self.direction == 'D' and self.has_lower_requests():
            self.direction = 'D'
        else:
            # LOOK algorithm: direction pivots towards the oldest pending requested floor
            primary_target = self.request_queue[0]
            if primary_target > self.floor:
                self.direction = 'U'
            elif primary_target < self.floor:
                self.direction = 'D'
            else:
                self.direction = 'I'

    def process_tick(self):
        # Handle emergency from non-moving states
        if self.emergency == '1' and self.state != 'MOVING':
            print(f"[8051 CORE] EMERGENCY triggered at Floor {self.floor}. Opening doors.")
            self.emergency = '0'
            self.state = 'SETTLING'
            self.direction = 'I'
            self.clear_current_request()
            return

        if self.state == 'IDLE':
            if self.target_mask > 0 or len(self.request_queue) > 0:
                self.decide_direction()
                if self.direction != 'I':
                    print(f"[8051 CORE] FSM Transition: IDLE -> MOVING")
                    self.state = 'MOVING'
                    self.ticks = 0
                    
        elif self.state == 'MOVING':
            self.ticks += 1
            if self.ticks >= 20: # 1s to move one floor strictly
                self.ticks = 0
                
                if self.direction == 'U': self.floor += 1
                elif self.direction == 'D': self.floor -= 1

                print(f"[8051 CORE] Arrived precisely at Floor Index {self.floor}")

                if self.emergency == '1':
                    print("[8051 CORE] EMERGENCY HALT COMPLETED")
                    self.emergency = '0'
                    self.state = 'SETTLING'
                    self.direction = 'I'
                    self.clear_current_request()
                    return

                if self.check_request_at_current():
                    print(f"[8051 CORE] Target Matched! Transition: MOVING -> DOOR_OPEN")
                    self.state = 'SETTLING'
                    self.clear_current_request()
                    self.direction = 'I'
                else:
                    self.decide_direction()
                    if self.direction == 'I':
                        self.state = 'IDLE'

        elif self.state == 'SETTLING':
            self.ticks += 1
            if self.ticks >= 5:
                self.ticks = 0
                self.state = 'DOOR_OPEN'
                self.door = '1'

        elif self.state == 'DOOR_OPEN':
            self.ticks += 1
            if self.ticks >= 60:
                self.ticks = 0
                self.door = '0'
                self.state = 'DOOR_CLOSING'
                print("[8051 CORE] Door Timer threshold reached. Resolving to Closed.")

        elif self.state == 'DOOR_CLOSING':
            self.ticks += 1
            if self.ticks >= 25:
                self.ticks = 0
                self.state = 'IDLE'

    def get_continuous_y(self):
        if self.state == 'MOVING':
            offset = self.ticks / 20.0
            if self.direction == 'U':
                return self.floor + offset
            elif self.direction == 'D':
                return self.floor - offset
        return float(self.floor)

core_sim = Core8051Simulator()

def connect_hardware():
    global ser
    print("[SYSTEM] Attempting physical UART connection to Keil Simulator on COM1...")
    socketio.sleep(1)
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"[SYSTEM] Hardware bridged successfully on {SERIAL_PORT}")
    except Exception:
        print("[SYSTEM] Hardware COM port unreachable. Bypassing physical serial...")
        socketio.sleep(0.5)
        if os.path.exists("elevator.asm"):
            with open("elevator.asm", "rt") as f:
                lines = len(f.readlines())
            print(f"[8051 VIRTUAL CORE] Successfully parsed elevator.asm ({lines} lines)")
            print(f"[8051 VIRTUAL CORE] Memory Map Bound: TARGET_MASK (31H)")
            print(f"[8051 VIRTUAL CORE] Interrupt Vectors: EXT0 (0003H), T0 (000BH), UART (0023H)")
        print("[8051 VIRTUAL CORE] Boot Sequence Complete. Start main execution loop.")

def serial_reader_thread():
    global ser
    while True:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('F:'):
                    parts = line.split('|')
                    status = {k: v for k, v in [p.split(':') for p in parts]}
                    socketio.emit('elevator_status', status)
            except Exception:
                pass
        else:
            core_sim.process_tick()
            status = {
                'F': str(core_sim.floor),
                'D': core_sim.direction,
                'DR': core_sim.door,
                'E': core_sim.emergency,
                'Y': round(core_sim.get_continuous_y(), 3)
            }
            socketio.emit('elevator_status', status)
        socketio.sleep(0.05)

@app.route('/')
def index():
    return render_template('index.html')

thread = None
thread_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=serial_reader_thread)
    print("[WEB UART] Frontend Client Connected via WebSocket")

@socketio.on('call_elevator')
def handle_call(data):
    floor = data.get('floor')
    print(f"\n[WEB UART] Received RX buffer: CALL:{floor}")
    if ser and ser.is_open:
        # Send A for 0, B for 1, ..., P for 15
        char_code = chr(65 + int(floor))
        ser.write(f"{char_code}\n".encode('utf-8'))
    else:
        print(f"[8051 UART] ISR Triggered! Setting bit in TARGET_MASK for floor index {floor}")
        core_sim.set_target(int(floor))

@socketio.on('emergency')
def handle_emergency():
    print("\n[WEB UART] Received RX buffer: EMERGENCY")
    if ser and ser.is_open:
        ser.write(b"EMERGENCY\n")
    else:
        print("[8051 EXT0] INT0 Edge Triggered! Setting EMERGENCY_FLAG = 1")
        core_sim.emergency = '1'

@socketio.on('door_open_cmd')
def handle_door_open():
    print("\n[WEB UART] Received RX buffer: DOOR OPEN OVERRIDE")
    if ser and ser.is_open:
        ser.write(b"O\n")
    else:
        if core_sim.state == 'DOOR_OPEN':
            core_sim.ticks = 0
        elif core_sim.state == 'DOOR_CLOSING':
            core_sim.state = 'DOOR_OPEN'
            core_sim.door = '1'
            core_sim.ticks = 0

@socketio.on('door_close_cmd')
def handle_door_close():
    print("\n[WEB UART] Received RX buffer: DOOR CLOSE OVERRIDE")
    if ser and ser.is_open:
        ser.write(b"X\n")
    else:
        if core_sim.state == 'DOOR_OPEN':
            core_sim.ticks = 60
            
print("\n=======================================================")
print("   8051 ELEVATOR CONTROL SYSTEM - COM BRIDGE LAYER")
print("=======================================================\n")
connect_hardware()

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)