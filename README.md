Alarm Fatigue Monitoring Prototype
=================================

Overview
--------
This repository contains a working prototype for an alarm-fatigue monitoring system. The system simulates patient vitals, runs lightweight ML/rule logic in a FastAPI backend, and drives physical alarms via an ESP32 gateway. It was built for demonstration and testing of alarm routing, alarm frequency, and basic alarm fatigue mitigation ideas.

Main components
---------------
- ESP32 #1 — Sensor Station (simulated):
  - Simulates HR, SpO2, temperature and `nurse_nearby` status.
  - Posts JSON to backend endpoint: `/api/sensor-data` every ~5s.
  - Periodically polls `/api/alarm-status` to display alarm status (LCD or Serial).
  - LEDs indicate WiFi/send status.

- ESP32 #2 — Alarm Gateway/Controller:
  - Polls backend `/api/alarm-status` every few seconds.
  - Activates physical alarm(s) (relay or direct buzzer pin) and LED indicators when an alarm is reported.
  - Hosts a small web server for manual testing: `/alarm/general`, `/alarm/critical`, `/alarm/stop`, `/status`.

- Backend — FastAPI (Python / Uvicorn):
  - Endpoints: `/api/sensor-data` (POST), `/api/alarm-status` (GET). WebSocket endpoint included for dashboard updates.
  - Loads ML models (if present) and performs policy/ML inference; returns JSON with fields like `general_alarm` and `critical_alarm`.
  - For testing, the backend was temporarily modified to return `general_alarm: true` every 2nd status request to exercise ESP behavior.

Where to find things in the repo
--------------------------------
- `backend/main.py` — FastAPI app, endpoints, ML integration and the temporary "force-true" test.
- `ESP sketches/` or user Arduino sketches — (ESP1 and ESP2 sketches) — the current working sketches are the ones you edited in the Arduino IDE (`health.ino` etc.).
- Arduino libraries: `C:\Users\Lenovo\Documents\Arduino\libraries\esp32-LiquidCrystal_I2C-master` — local LCD library used (patched locally).

How to run (Windows PowerShell)
-------------------------------
1. Activate project virtualenv and run backend (from project folder):

```powershell
cd "C:\Users\Lenovo\Desktop\Alarm fatigue #prototype\backend"
# If you use the created venv
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Confirm backend is up by opening in a browser (replace IP if your PC has a different local IP):

```
http://localhost:8000/docs
# or
http://192.168.223.101:8000/docs
```

3. Upload ESP sketches
- ESP32 #1 (Sensor station): open the sensor sketch in Arduino IDE, set WiFi SSID/password and backend IP (`serverURL` and `alarmStatusURL`), and flash.
- ESP32 #2 (Alarm gateway): open the gateway sketch, set WiFi and backend URL, choose whether you use relay pins (GPIO 26/27) or direct buzzer pin (GPIO 25) and flash.

4. Optional: Serve the frontend (dashboard)
- In the `landing page` folder, run a simple HTTP server to view the dashboard:

```powershell
cd "C:\Users\Lenovo\Desktop\Alarm fatigue #prototype\landing page"
python -m http.server 3000
```

Then open `http://localhost:3000` in a browser.

Hardware wiring summary
-----------------------
- ESP32 #1 (Sensor station):
  - I2C: SDA=21, SCL=22 shared for LCD and MAX30100 (if used)
  - LM35 analog -> GPIO34 (LM35_PIN)
  - LEDs as in sketch (GREEN_LED=2, RED_LED=4, YELLOW_LED=5)

- ESP32 #2 (Gateway):
  - Relay controls (if used): RELAY1_PIN=26 (general), RELAY2_PIN=27 (critical)
  - Or direct buzzer: BUZZER_PIN=25 (if you removed relay)
  - LEDs: BLUE_LED=2 (WiFi), ORANGE_LED=18 (alarm), WHITE_LED=19 (system ready)

LCD (I2C) notes & fix
---------------------
- The local library `esp32-LiquidCrystal_I2C-master` provides a C-style API (functions named `LCDI2C_*`) and expects explicit SDA/SCL pins when initializing: `LCDI2C_init(0x27,16,2,21,22);`.
- If you used a different `LiquidCrystal_I2C` library (Arduino-style object `LiquidCrystal_I2C lcd(...)`), that can cause incompatibilities.
- Compilation error fix done locally: the library used `ets_delay_us()` which is deprecated; changed calls to `esp_rom_delay_us()` in `LiquidCrystal_I2C.c` to work with modern ESP32 Arduino core.
  - File patched: `C:\Users\Lenovo\Documents\Arduino\libraries\esp32-LiquidCrystal_I2C-master\LiquidCrystal_I2C.c` (replace `ets_delay_us` → `esp_rom_delay_us`).

How the alarm flow works (quick)
--------------------------------
1. ESP1 sends vitals: POST /api/sensor-data.
2. Backend processes (ML/rules) and makes a decision.
3. ESP2 polls GET /api/alarm-status:
   - If `general_alarm: true` or `critical_alarm: true` → ESP2 calls `activateAlarm()` (drive buzzer/relay + LED).
   - When flags are false, ESP2 stops alarms or runs the 'no-alarm' LED/beep sequence.
4. ESP1 also polls alarm-status and displays status on LCD/Serial.

Common problems & fixes
-----------------------
- HTTPClient returns `-1` or POST fails:
  - Backend not running or firewall blocking port 8000.
  - Wrong IP in sketch (use local machine IP or host reachable by ESP).
  - Ensure all devices (PC and ESPs) are on same network.

- LCD compile errors:
  - Use the ESP32-specific library or johnrickman/marcoschwartz `LiquidCrystal_I2C` that supports ESP32.
  - If library uses `ets_delay_us`, replace with `esp_rom_delay_us`.

- Backend not triggering alarms:
  - ML/rule thresholds not met by simulated data.
  - For testing, backend has a temporary mode to force `general_alarm:true` every 2nd `/api/alarm-status` call. Remove this after testing.

Testing steps (smoke test)
--------------------------
1. Start backend and confirm `/docs` opens.
2. Flash ESP1; monitor Serial — it should show readings and successful POST responses (200).
3. Flash ESP2; open `http://<esp2_ip>/` to use manual alarm buttons. Observe relay/buzzer activation and LED states.
4. Use backend forced-true or trigger conditions that produce `general_alarm:true`; ESP2 should start the buzzer/relay.

Next improvements
----------------
- Add a dashboard page showing live vitals and alarm history.
- Improve backend policy to avoid frequent false positives and add rate-limiting of alarms to reduce fatigue.
- Add persistent logging of alarm events to a file or DB for analysis.
- Add unit tests for backend ML mapping and a Dockerfile for easier deployment.

Want a polished README or a one-page demo handout?
-------------------------------------------------
I can generate a 1-page demo handout (PDF/Markdown) summarizing hardware, how to demo, and talking points. Tell me whether you want a concise handout or keep the README as-is and I will produce the handout next.

---
Progress: created README draft and updated the todo list (created). Next: I can produce the one-page demo handout if you want, or push the README into the repo (already created). Which would you like next?