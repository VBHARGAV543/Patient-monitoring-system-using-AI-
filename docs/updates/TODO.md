# TODO: Patient-Centric Alarm System Refactor

## 🔒 ARCHITECTURE DECISIONS (DO NOT CHANGE)

- Use **ONE physical band** (`BAND_01`) reused across demos
- System works with **sequential patients**, not parallel
- Band = **prototype sensing node**, NOT clinical device
- All **intelligence + tampering** happens in the **backend**, not on the band
- Core switch is `patient_type`: `GENERAL` vs `CRITICAL`
- Every demo follows: **ADMIT → MONITOR → (ALERT) → DISCHARGE**

---

## 1️⃣ DATABASE CHANGES

### Create/Update `patients` table:
```sql
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    problem TEXT NOT NULL,
    patient_type TEXT NOT NULL CHECK(patient_type IN ('GENERAL', 'CRITICAL')),
    status TEXT NOT NULL CHECK(status IN ('ADMITTED', 'MONITORING', 'DISCHARGED')),
    admitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discharged_at TIMESTAMP NULL
);
```

### Create `band_assignment` table:
```sql
CREATE TABLE band_assignment (
    band_id TEXT PRIMARY KEY,
    patient_id TEXT,
    active BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
```

### Create `alarm_events` log table:
```sql
CREATE TABLE alarm_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    patient_type TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('NONE', 'GENERAL', 'CRITICAL')),
    was_suppressed BOOLEAN DEFAULT FALSE,
    reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
```

**Files to modify:**
- [ ] `backend/database.py` - Add tables and helper functions

---

## 2️⃣ BACKEND: PATIENT LIFECYCLE & BINDING

### Add new endpoints:

#### `POST /api/patient/admit`
```python
# Body: {"name": str, "age": int, "problem": str, "patient_type": "GENERAL"|"CRITICAL"}
# - Creates patient row (status = ADMITTED)
# - Updates band_assignment (band_id = BAND_01, active = true)
# - Returns patient_id
```

#### `POST /api/patient/discharge`
```python
# Body: {"patient_id": str}
# - Sets patients.status = DISCHARGED
# - Sets band_assignment.active = false
# - Returns success message
```

#### `GET /api/patient/active`
```python
# Returns list of current admitted/monitoring patients
```

#### `GET /api/patient/{patient_id}`
```python
# Returns patient details and recent vitals
```

**Files to modify:**
- [ ] `backend/main.py` - Add new endpoints
- [ ] `backend/database.py` - Add query functions

---

## 3️⃣ BACKEND: SENSOR INGEST + PATIENT BINDING

### Update `POST /api/sensor-data` handler:

**Current behavior:** Receives raw vitals, applies random tampering

**New behavior:**
1. Accept JSON from band: `{"band_id": "BAND_01", "hr": 78, "temp": 36.8, "spo2": 98, "timestamp": 123456}`
2. Look up current `patient_id` via `band_assignment` where `band_id = "BAND_01"` and `active = true`
3. If no active patient → return error "Band not assigned"
4. Fetch patient details from `patients` table
5. Pass everything to alarm policy module

**Important:** Band sends only REAL/raw values. No faking at firmware level.

**Files to modify:**
- [ ] `backend/main.py` - Update `/api/sensor-data` endpoint
- [ ] Remove or comment out current `generate_random_patient_profile()` logic
- [ ] Keep tampering logic but tie it to actual patient context

---

## 4️⃣ BACKEND: ALARM POLICY MODULE

### Create new file: `backend/alarm_policy.py`

```python
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AlarmDecision:
    general_alarm: bool
    critical_alarm: bool
    reason: str
    was_suppressed: bool

def evaluate_alarm(patient: Dict, vitals: Dict, demo_profile: str = "NORMAL") -> AlarmDecision:
    """
    Main alarm logic - branches based on patient_type
    
    Args:
        patient: Dict with patient_id, patient_type, age, problem
        vitals: Dict with HR, SpO2, Temp, etc.
        demo_profile: "NORMAL" | "GENERAL_TAMPER" | "CRITICAL_TAMPER"
    
    Returns:
        AlarmDecision with alarm flags and reasoning
    """
    
    # Branch logic based on patient_type
    if patient["patient_type"] == "GENERAL":
        # Implement suppression logic:
        # - Wider thresholds
        # - Debounce window
        # - Ignore minor anomalies
        pass
    
    elif patient["patient_type"] == "CRITICAL":
        # Minimal suppression:
        # - Strict thresholds
        # - Immediate escalation
        # - No proximity filtering
        pass
    
    # Apply demo_profile if needed for scripted demos
    
    return AlarmDecision(...)
```

**Files to create:**
- [ ] `backend/alarm_policy.py` - Core alarm logic module

**Files to modify:**
- [ ] `backend/main.py` - Import and use `evaluate_alarm()`

---

## 5️⃣ BACKEND: REMOVE TESTING HACKS

### Clean up `backend/main.py`:

- [ ] **Remove line 22:** `alarm_toggle_counter = 0`
- [ ] **Remove/modify `/api/alarm-status` forced toggle logic (lines 265-283)**
  - Option A: Delete entirely, replace with proper alarm_policy call
  - Option B: Gate behind `DEMO_FORCE_ALARM` environment variable (default False)

```python
# BEFORE (lines 265-283):
global alarm_toggle_counter
alarm_toggle_counter += 1
if alarm_toggle_counter % 2 == 0:
    return {"general_alarm": True, ...}

# AFTER:
# Look up active patient
# Get latest vitals
# Call alarm_policy.evaluate_alarm()
# Return actual decision
```

**Files to modify:**
- [ ] `backend/main.py` - Remove testing code

---

## 6️⃣ FRONTEND / UI CHANGES

### Create Patient Admission Form

**New file:** `landing page/admit.html`

Form fields:
- Name (text input)
- Age (number input)
- Problem/Reason for admission (textarea)
- Patient Type (dropdown: GENERAL / CRITICAL)
- Submit button → calls `POST /api/patient/admit`

### Update Dashboard (`landing page/index.html`)

**Left Panel:** Patient list
- Fetch from `GET /api/patient/active`
- Display: Name, Age, Type (badge), Status indicator
- Click to select patient

**Right Panel:** Patient details
- Show selected patient info
- Current vitals (from WebSocket or polling)
- Alert status indicator:
  - 🟢 Green = stable
  - 🟠 Amber = warnings/suppressed
  - 🔴 Red = active critical alarm
- **Discharge button** → calls `POST /api/patient/discharge`

**Files to create:**
- [ ] `landing page/admit.html` - Admission form
- [ ] `landing page/admit.js` - Form logic

**Files to modify:**
- [ ] `landing page/index.html` - Update layout
- [ ] `landing page/script.js` - Add patient list and detail views
- [ ] `landing page/style.css` - Add styling

---

## 7️⃣ BAND FIRMWARE CHANGES

### Update ESP32 #1 sensor code

**Current behavior:** Simulates 4 scenarios with hardcoded values

**New behavior:**
1. Read **real sensor values** (MAX30100 for HR/SpO2, LM35 for temp)
2. Send periodic JSON: `{"band_id": "BAND_01", "hr": <real>, "temp": <real>, "spo2": <real>}`
3. **Remove all simulation/tampering logic from firmware**
4. Optional: Add button to inject noise for demo (but keep it realistic)

**Important:** All patient context (general vs critical) is decided by backend using `patient_type`.

**Files to modify:**
- [ ] ESP32 firmware (Arduino sketch) - Replace simulation with real sensor reads
- [ ] Keep LED indicators for WiFi/send status

---

## 8️⃣ LOGGING & EVALUATION

### Implement alarm event logging

In `alarm_policy.py` or `backend/main.py`:
- Every time `evaluate_alarm()` is called, log to `alarm_events` table
- Capture: patient_id, timestamp, patient_type, decision, was_suppressed, reason

### Add statistics endpoint

**New endpoint:** `GET /api/stats/alarms`
```python
# Returns:
# - Total alarms by type
# - Suppression rate for GENERAL vs CRITICAL
# - Average alarms per patient
# - Time-series data for graphs
```

**Files to modify:**
- [ ] `backend/alarm_policy.py` - Add logging
- [ ] `backend/main.py` - Add stats endpoint

---

## 9️⃣ DOCUMENTATION UPDATES

### Update `README.md`

Add section explaining:
- System uses **one reusable prototype band** (`BAND_01`)
- Patients are managed via **admit/discharge** flow
- `patient_type` (`GENERAL` vs `CRITICAL`) controls alarm behavior
- Wearable is **proof-of-concept**, not clinical device
- Main contribution is **context-aware alarm orchestration**

### Add inline comments

In `backend/main.py` and `alarm_policy.py`:
- Document why patient_type drives logic
- Explain suppression strategies
- Clarify demo_profile usage

**Files to modify:**
- [ ] `README.md` - Add architecture explanation
- [ ] `backend/main.py` - Add comments
- [ ] `backend/alarm_policy.py` - Add docstrings

---

## 🎯 IMPLEMENTATION PRIORITY

### Phase 1: Database & Backend Core (Week 1)
- [ ] 1.1: Database schema changes
- [ ] 1.2: Admit/discharge endpoints
- [ ] 1.3: Band assignment logic
- [ ] 1.4: Remove alarm_toggle_counter

### Phase 2: Alarm Policy (Week 2)
- [ ] 2.1: Create alarm_policy.py module
- [ ] 2.2: Implement patient_type branching
- [ ] 2.3: Add demo_profile tampering
- [ ] 2.4: Event logging

### Phase 3: Frontend (Week 3)
- [ ] 3.1: Admit patient form
- [ ] 3.2: Patient list view
- [ ] 3.3: Patient details panel
- [ ] 3.4: Discharge button
- [ ] 3.5: Alert indicators

### Phase 4: Hardware & Polish (Week 4)
- [ ] 4.1: Update ESP32 firmware
- [ ] 4.2: Test with real sensors
- [ ] 4.3: Documentation updates
- [ ] 4.4: End-to-end testing

---

## ✅ TESTING CHECKLIST

- [ ] Can admit a GENERAL patient
- [ ] Can admit a CRITICAL patient
- [ ] Band correctly binds to active patient
- [ ] Sensor data flows: Band → Backend → Policy → Decision
- [ ] GENERAL patient has suppressed alarms
- [ ] CRITICAL patient has sensitive alarms
- [ ] Can discharge patient and reassign band
- [ ] Frontend shows real-time vitals
- [ ] Alarm events are logged to database
- [ ] Stats endpoint returns correct metrics

---

## 📝 NOTES

- Keep existing ML models (`critical_model.pkl`, `general_model.pkl`)
- Reuse `tamper_real_readings()` logic but tie to patient context
- Demo profiles are for presentations, not production
- Focus on **architecture quality** over sensor accuracy

---

**Created:** December 10, 2025  
**Project:** Patient Monitoring System using AI  
**Owner:** VBHARGAV543
