document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const topDisplay = document.getElementById('top-display');
    const panelDisp = document.getElementById('panel-disp');
    const outsideWall = document.getElementById('outside-wall');
    const doorsFrame = document.getElementById('doors-frame');
    const emergencyBtn = document.getElementById('emergency-btn');
    const doorOpenBtn = document.getElementById('door-open-btn');
    const doorCloseBtn = document.getElementById('door-close-btn');
    const callBtns = document.querySelectorAll('.call-btn');
    const connStatus = document.getElementById('conn-status');
    
    // New diagnostics bindings
    const cabinExternal = document.getElementById('cabin-external');
    const cabinDisp = document.getElementById('cabin-disp');
    const rawLog = document.getElementById('raw-log');

    socket.on('connect', () => {
        connStatus.textContent = 'Hardware Connected';
        connStatus.classList.remove('disconnected');
    });
    socket.on('disconnect', () => {
        connStatus.textContent = 'Hardware DISCONNECTED';
        connStatus.classList.add('disconnected');
    });

    callBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const floor = parseInt(btn.getAttribute('data-floor'));
            // Light up the incandescent button rim
            btn.classList.add('active-call'); 
            socket.emit('call_elevator', { floor: floor });
        });
    });

    emergencyBtn.addEventListener('click', () => {
        socket.emit('emergency');
    });

    if (doorOpenBtn) {
        doorOpenBtn.addEventListener('click', () => {
            socket.emit('door_open_cmd');
        });
    }

    if (doorCloseBtn) {
        doorCloseBtn.addEventListener('click', () => {
            socket.emit('door_close_cmd');
        });
    }

    socket.on('elevator_status', (data) => {
        // Update raw log
        const strForm = Object.entries(data)
            .filter(([k,v]) => k !== 'Y')
            .map(([k,v]) => `${k}:${v}`).join('|');
        if(rawLog) rawLog.textContent = strForm;

        const f = parseInt(data['F']);
        const yPos = data.Y !== undefined ? parseFloat(data.Y) : f;
        const closestF = Math.round(yPos);
        const d = data['D']; // U, D, I
        let dirIcon = '';
        if (d === 'U') dirIcon = '▲';
        else if (d === 'D') dirIcon = '▼';
        else dirIcon = ' ';

        const displayF = closestF === 0 ? 'G' : closestF;

        if (closestF >= 0 && closestF <= 15) {
            topDisplay.textContent = `${displayF} ${dirIcon}`;
            panelDisp.textContent = `${displayF} ${dirIcon}`;
            outsideWall.textContent = closestF === 0 ? `GROUND` : `FLOOR ${closestF}`;
            
            // External shaft tracking
            if(cabinDisp) cabinDisp.textContent = displayF;
            if(cabinExternal) {
                const maxCameraY = 640 - 360;
                let cameraY = (yPos - 4) * 40;
                if (cameraY < 0) cameraY = 0;
                if (cameraY > maxCameraY) cameraY = maxCameraY;
                
                const cabinWorldY = yPos * 40;
                const cabinVisualY = cabinWorldY - cameraY;
                
                const shaftFloors = document.getElementById('shaft-floors');
                if(shaftFloors) shaftFloors.style.bottom = `-${cameraY}px`;
                
                cabinExternal.style.bottom = `${cabinVisualY}px`;
            }
            
            // Turn off the incandescent bulb if the 8051 door opens at this floor
            if (data['DR'] === '1') {
                callBtns.forEach(btn => {
                    if (parseInt(btn.getAttribute('data-floor')) === f) {
                        btn.classList.remove('active-call');
                    }
                });
            }
        }

        const dr = data['DR'];
        if (dr === '1') {
            doorsFrame.classList.add('door-open');
            if(cabinExternal) cabinExternal.classList.add('door-open');
        } else {
            doorsFrame.classList.remove('door-open');
            if(cabinExternal) cabinExternal.classList.remove('door-open');
        }

        const e = data['E'];
        if (e === '1') {
            emergencyBtn.classList.add('emergency-mode-active');
            if(cabinExternal) cabinExternal.classList.add('emergency-mode');
        } else {
            emergencyBtn.classList.remove('emergency-mode-active');
            if(cabinExternal) cabinExternal.classList.remove('emergency-mode');
        }
    });
});
