# Patient Monitoring System Using AI

A full-stack, real-time hospital patient monitoring system covering a **FastAPI backend**, **React web frontend**, and **Android Kotlin mobile app** for nurses. Supports two operating modes — hardware (real ESP32 sensors) and simulation (AI-driven synthetic vitals) — with a complete ML pipeline for alarm classification.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Hardware Components](#2-hardware-components)
3. [Machine Learning Pipeline](#3-machine-learning-pipeline)
4. [NEWS2 Scoring Algorithm](#4-news2-scoring-algorithm)
5. [Training Data Generation](#5-training-data-generation)
6. [Vital Estimator (Hardware Mode)](#6-vital-estimator-hardware-mode)
7. [Disease Profile System](#7-disease-profile-system)
8. [Alarm Policy Engine](#8-alarm-policy-engine)
9. [Backend (FastAPI)](#9-backend-fastapi)
10. [Database Schema (Supabase PostgreSQL)](#10-database-schema-supabase-postgresql)
11. [Web Frontend (React + Vite)](#11-web-frontend-react--vite)
12. [Mobile App (Android Kotlin)](#12-mobile-app-android-kotlin)
13. [Network & Configuration](#13-network--configuration)
14. [What Was Achieved](#14-what-was-achieved)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────┐
│              HARDWARE LAYER (Optional)               │
│   ESP32 ── MAX30102 (HR + SpO2) ── DS18B20 (Temp)   │
│          Sends JSON via HTTP POST /api/sensor/data   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         BACKEND  (Python FastAPI, Port 8000)         │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │ ML Predictor │  │ Disease Prof. │  │ Alarm    │  │
│  │ Random Forest│  │ + Vital Sim.  │  │ Policy   │  │
│  └──────────────┘  └───────────────┘  └──────────┘  │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │ Camera Mgr   │  │ Database Layer │  │ WebSocket│  │
│  │ (OpenCV)     │  │ (asyncpg)     │  │ /ws      │  │
│  └──────────────┘  └───────────────┘  └──────────┘  │
│              Supabase PostgreSQL (cloud)             │
└──────┬──────────────────────────────┬───────────────┘
       │ HTTP REST + WebSocket        │ HTTP REST
       ▼                              ▼
┌─────────────────┐       ┌──────────────────────────┐
│  Web Frontend   │       │  Android Mobile App       │
│  React + Vite   │       │  Kotlin + Coroutines      │
│  Port 3000      │       │  Nurse Alarm App          │
└─────────────────┘       └──────────────────────────┘
```

**Communication:**
- Backend ↔ Frontend: REST API + WebSocket (`/ws`)
- Backend ↔ Mobile: REST API polling + WebSocket
- ESP32 ↔ Backend: HTTP POST to `/api/sensor/data`
- Camera: OpenCV captures frames in background thread; `/snapshot` returns latest JPEG (<10 ms response)

---

## 2. Hardware Components

| Component | Role | Interface |
|---|---|---|
| **ESP32 Microcontroller** | Main MCU, sends sensor data over WiFi | HTTP POST JSON |
| **MAX30102** | Measures Heart Rate (HR) and SpO2 (blood oxygen) | I2C |
| **DS18B20** | Measures body temperature (Temp) in °C | OneWire |

**Hardware Mode Flag:** Each patient admission has `hardware_mode: bool`. When `true`, only HR, SpO2, and Temp arrive from real sensors; the remaining 4 vitals (BP_sys, BP_dia, RR, Glucose) are **estimated by ML regression models** (see §6).

---

## 3. Machine Learning Pipeline

Two separate classification pipelines exist — one for General Ward and one for Critical Ward.

### Pipeline Overview

```
Raw Vitals (7 signals)
        │
        ▼
  NEWS2 Scorer  ──────────────────────────────────────────┐
  (deterministic, rule-based)                             │
        │                                                 │
        ▼                                                 │
  profile_adjusted_label()                               │
  (disease + medication adjustments)                      │
        │                                                 │
        ▼                                                 │
  Synthetic Training Data                                 │
  (MIMIC-grounded Gaussian distributions)                 │
        │                                                 │
        ▼                                                 │
  Random Forest Classifier                               │
  (n_estimators=200, max_depth=12, balanced)             │
        │                                                 ▼
        │                              Feature vector built
        │                              at inference time
        ▼                              (same feature engineering)
  Label: 0=Safe / 1=Warning / 2=Critical
```

### Models

| Model | Ward | Features | Algorithm | Training Samples |
|---|---|---|---|---|
| `general_model.pkl` | General | 19 features | RandomForestClassifier | 8,000 |
| `critical_model.pkl` | Critical | 20 features | RandomForestClassifier | 8,000 |
| `vital_estimator.pkl` | Both | 17 features | RandomForestRegressor × 4 | 16,000 |

### Model Hyperparameters (General & Critical Classifiers)
```python
RandomForestClassifier(
    n_estimators = 200,
    max_depth    = 12,
    min_samples_leaf = 4,
    class_weight = "balanced",   # handles class imbalance
    random_state = 42,
    n_jobs       = -1,           # all CPU cores
)
```

### General Ward Feature Vector (19 features)
```
HR, SpO2, Temp, BP_sys, BP_dia, RR, Glucose,
news2_score, age,
has_bp_med, has_glucose_med, has_bronchodilator, has_antibiotic, has_allergy_flag,
disease_Diabetes Type 2, disease_Gastroenteritis,
disease_Hypertension, disease_Mild Pneumonia, disease_UTI
```

### Critical Ward Feature Vector (20 features)
```
HR, SpO2, Temp, BP_sys, BP_dia, RR, Glucose,
ECG_abnormal, neuro_score, news2_score, age,
has_vasopressor, has_anticoagulant, has_antibiotic, has_bp_med, has_allergy_flag,
disease_Heart Attack, disease_Sepsis, disease_Severe Pneumonia, disease_Stroke
```

---

## 4. NEWS2 Scoring Algorithm

**Source:** Royal College of Physicians (2017) — National Early Warning Score 2  
**URL:** https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2

NEWS2 is the **base alarm label generator** used to create training labels. The Random Forest then learns patient-specific adjustments on top of this deterministic baseline.

### Scoring Table

| Parameter | Score 3 | Score 2 | Score 1 | Score 0 | Score 1 | Score 2 | Score 3 |
|---|---|---|---|---|---|---|---|
| **Respiratory Rate** | ≤8 | — | 9–11 | 12–20 | — | 21–24 | ≥25 |
| **SpO2 (%)** | ≤91 | 92–93 | 94–95 | ≥96 | — | — | — |
| **BP Systolic** | ≤90 | 91–100 | 101–110 | 111–219 | — | — | ≥220 |
| **Heart Rate** | ≤40 | — | 41–50 | 51–90 | 91–110 | 111–130 | ≥131 |
| **Consciousness** | — | — | — | Alert | — | — | Any abnormality (+3) |
| **Temperature (°C)** | ≤35.0 | — | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | ≥39.1 | — |

**Total Range:** 0 – 20

### Risk Levels
| Score | Risk | Label Int |
|---|---|---|
| 0–4 | LOW | 0 (Safe) |
| 5–6 | MEDIUM | 1 (Warning) |
| ≥7 | HIGH | 2 (Critical) |

### Personalised Adjustments (`profile_adjusted_label`)

The key innovation: the **same raw vitals** → different alarm level depending on disease and medication context.

```python
def profile_adjusted_label(base_score, disease, medications, vitals, age) -> int:
```

**Adjustment rules applied on top of NEWS2 base score:**

| Condition | Rule | Score Δ |
|---|---|---|
| Hypertension + BP med + BP_sys > 155 | Drug failing → escalate | +2 |
| Hypertension + BP med + BP_sys > 145 | Borderline failure | +1 |
| Diabetes + glucose med + Glucose > 220 | Medication failing | +3 |
| Diabetes + glucose med + Glucose > 180 | Borderline | +1 |
| Asthma + bronchodilator + SpO2 < 90 | Bronchodilator failed → critical | +3 |
| Asthma + bronchodilator + SpO2 < 93 | Borderline | +2 |
| Pneumonia/Sepsis + antibiotic + Temp > 39.5 | Drug not working | +2 |
| Pneumonia/Sepsis + antibiotic + Temp > 38.8 | Borderline | +1 |
| Age ≥ 70 AND adjusted_score ≥ 3 | Elderly risk amplification | +1 |
| Age ≥ 80 AND adjusted_score ≥ 2 | Extra elderly amplification | +1 |

**Medication detection** (string matching on medication names):
- BP meds: amlodipine, losartan, lisinopril, hydrochlorothiazide, metoprolol, ramipril
- Glucose meds: metformin, insulin, glipizide, glibenclamide, sitagliptin
- Bronchodilators: salbutamol, albuterol, budesonide, montelukast, ipratropium, salmeterol
- Antibiotics: amoxicillin, azithromycin, levofloxacin, meropenem, ceftriaxone, vancomycin, ciprofloxacin, piperacillin

---

## 5. Training Data Generation

Data is **synthetic** but grounded in MIMIC-III-like clinical distributions. Each disease has defined Gaussian parameters for vital signs.

### General Ward Diseases & Vital Baselines

| Disease | HR (mean±sd) | SpO2 | Temp | BP_sys | Notable |
|---|---|---|---|---|---|
| Hypertension | 80±12 | 97±1.5 | 36.8±0.3 | 148±18 | BP_med reduces BP_sys by 10–18 |
| Diabetes Type 2 | 82±13 | 96±2 | 36.9±0.4 | 132±15 | Glucose 185±50 |
| Asthma | 94±14 | 91±3.5 | 37.0±0.4 | 122±12 | SpO2 critically low |
| Mild Pneumonia | 96±14 | 92±3 | 38.6±0.7 | 118±14 | Fever + tachycardia |
| UTI | 90±12 | 97±1 | 38.0±0.6 | 124±14 | — |
| Gastroenteritis | 95±14 | 97±1 | 37.8±0.6 | 108±16 | Low BP (dehydration) |

### Critical Ward Diseases & Vital Baselines

| Disease | HR | SpO2 | BP_sys | Notable |
|---|---|---|---|---|
| Heart Attack | 108±20 | 93±4 | 95±22 | ECG 70% abnormal, neuro 14±1 |
| Stroke | 88±16 | 94±3.5 | 165±25 | Neuro score 8±4 (impaired) |
| Severe Pneumonia | 108±18 | 86±5 | 108±18 | High fever 39.5±0.9 |
| Sepsis | 118±18 | 90±5 | 82±18 | Critically low BP |
| Acute Respiratory Failure | 112±18 | 84±6 | 105±20 | RR 32±8 |

### Sample Generation Process
1. Sample raw vitals from disease-specific Gaussian distributions
2. Clip to physiological bounds (e.g. SpO2 70–100, HR 25–220)
3. With 78–82% probability, apply a medication — adjusting vitals by medication effect
4. Clip again after medication adjustment
5. Compute NEWS2 score from final vitals
6. Apply `profile_adjusted_label()` → final label (0/1/2)
7. Build full feature vector → record stored

**Total training data per model:** 8,000 samples (general) + 8,000 (critical)  
**Train/Test split:** 80/20, stratified by label  
**Cross-validation:** 5-fold, scored by F1-macro

---

## 6. Vital Estimator (Hardware Mode)

**File:** `ML/train_vital_estimator.py` → produces `backend/vital_estimator.pkl`

When real hardware is used, only 3 vitals are measured. The other 4 are **estimated by regression**:

| Real Sensors | Estimated |
|---|---|
| HR (MAX30102) | BP_sys |
| SpO2 (MAX30102) | BP_dia |
| Temp (DS18B20) | RR (Respiratory Rate) |
| — | Glucose |

### Estimator Feature Vector (17 features)
```
HR, SpO2, Temp, news2_partial, age, is_critical,
disease_Hypertension, disease_Diabetes Type 2, disease_Asthma,
disease_Mild Pneumonia, disease_UTI, disease_Gastroenteritis,
disease_Heart Attack, disease_Stroke, disease_Severe Pneumonia,
disease_Sepsis, disease_Acute Respiratory Failure
```

`news2_partial` = partial NEWS2 score using only HR, SpO2, Temp (max 8 pts of 20).

### Partial NEWS2 Formula (3-sensor variant)
```python
score = 0
# SpO2
if spo2 <= 91:   score += 3
elif spo2 <= 93: score += 2
elif spo2 <= 95: score += 1
# Heart Rate
if hr <= 40:     score += 3
elif hr <= 50:   score += 1
elif hr <= 90:   score += 0
elif hr <= 110:  score += 1
elif hr <= 130:  score += 2
else:            score += 3
# Temperature
if temp <= 35.0: score += 3
elif temp <= 36.0: score += 1
elif temp <= 38.0: score += 0
elif temp <= 39.0: score += 1
else:            score += 2
```

### Estimator Model
```python
RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
# Separate model per each of the 4 targets
```

Fallback when `.pkl` is missing: clinical safe defaults — BP_sys=120, BP_dia=80, RR=16, Glucose=100.

---

## 7. Disease Profile System

**File:** `backend/disease_profiles.py`

Provides realistic disease profiles with symptoms, vital impact ranges, and medication effects. Used at admission to generate the patient's baseline state.

### General Ward Diseases (7)
- Pneumonia (Mild) — antibiotics (Amoxicillin, Azithromycin)
- UTI — antibiotics (Ciprofloxacin, Nitrofurantoin)
- Gastroenteritis — IV fluids, Ondansetron
- Asthma (Mild Attack) — Albuterol inhaler, Prednisone
- Cellulitis — Cephalexin, Clindamycin
- Migraine — Sumatriptan, Ibuprofen
- Hypertension / Diabetes Type 2 / others via `disease_profiles.py`

### Critical Ward Diseases (5+)
- Myocardial Infarction — Aspirin, Nitroglycerin, Morphine, Metoprolol
- Septic Shock — Norepinephrine IV, IV Fluids, Broad-spectrum antibiotics
- ARDS — High-flow O2/Mechanical Ventilation, Dexamethasone, Prone Positioning
- Stroke (Ischemic) — Alteplase, Labetalol
- Heart Attack, Severe Pneumonia

Each medication has a `vitals_effect` dict specifying exactly how it modifies vitals (e.g. Norepinephrine: BP_sys +40, BP_dia +25, HR +10).

### Patient Body Strength & Genetics
| Parameter | Values | Effect |
|---|---|---|
| `body_strength` | strong / average / weak | Modulates vital stability |
| `genetic_condition` | healthy / hypertension_prone / diabetes_prone | Adjusts disease baseline |

---

## 8. Alarm Policy Engine

**File:** `backend/alarm_policy.py`

### Alarm Suppression Logic

**General Ward** — aggressive suppression (reduce false alarms):
```
if ML predicts 0 (safe) → always suppress
if < 2 critical vitals → suppress
Critical thresholds:  HR > 130 or < 50
                      SpO2 < 88
                      Temp > 39.5 or < 35
                      BP_sys > 180 or < 90
```

**Critical Ward** — minimal suppression:
```
if ML predicts 0 (safe) → suppress
otherwise → always alarm
```

### Demo Mode Tampering (for presentations)

| Scenario | GENERAL vitals | CRITICAL vitals |
|---|---|---|
| NORMAL | No change | No change |
| MILD_DETERIORATION | BP 140–155, Temp 37.5–38.2, HR 90–105 | HR 110–130, SpO2 88–92, BP 160–175 |
| CRITICAL_EMERGENCY | BP 180–200, Temp 39.5–40.5, HR 120–140 | HR 150–180, SpO2 75–85, BP 200–220, Temp 40–41 |
| FALSE_POSITIVE | HR=59 or 101, BP_sys=139 or 141, SpO2=94 or 95 | Edge-of-normal values |

### Alarm Decision Output
```python
class AlarmDecision:
    should_alarm: bool
    alarm_level: str        # "LOW" / "MEDIUM" / "HIGH"
    alert_message: str
    requires_proximity: bool
    ml_prediction: int      # 0/1/2
    news2_score: int
```

---

## 9. Backend (FastAPI)

**File:** `backend/main.py` — 1,487 lines  
**Server:** uvicorn, Port 8000, `--host 0.0.0.0`

### Key REST Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Server health + IP info |
| `POST` | `/api/patient/admit` | Admit new patient |
| `GET` | `/api/patient/active` | Get currently active patient |
| `GET` | `/api/patients/admitted` | List admitted patients (with `?patient_type=CRITICAL`) |
| `POST` | `/api/patient/{id}/discharge` | Discharge a patient |
| `GET` | `/api/patient/{id}/vitals/latest` | Latest vital signs log |
| `GET` | `/api/patient/{id}/alarm-history` | Alarm event history |
| `POST` | `/api/sensor/data` | Receive real sensor data from ESP32 |
| `POST` | `/api/predict` | Direct ML prediction endpoint |
| `GET` | `/snapshot` | Latest camera JPEG frame |
| `GET` | `/stream` | MJPEG camera stream |
| `POST` | `/api/band/reset` | Release band assignment |
| `POST` | `/api/nurse/register` | Register nurse session |
| `PUT` | `/api/nurse/{id}/proximity` | Update nurse BLE proximity |
| `WebSocket` | `/ws` | Real-time events to clients |
| `GET` | `/api/network-info` | Get network IP/port info |

### Patient Admission Flow
```
POST /api/patient/admit
          │
          ├─ Validate band availability (only 1 active patient allowed)
          ├─ Pack staff JSON into emergency_contact if CRITICAL ward
          ├─ If disease specified → generate disease profile (vitals_impact, medications)
          ├─ Else if demo_mode → generate mock demographic data
          ├─ Create patient record in DB
          ├─ Assign BAND_01 to patient
          ├─ Initialize VitalSignsSimulator (or wait for sensor data)
          └─ Start vital generation loop
```

### Staff Assignment (Critical Ward)
When admitting a CRITICAL patient with doctor/nurse names:
```python
staff_data = {
    "doctor_primary":   patient.doctor_primary,
    "nurse_assigned":   patient.nurse_assigned,
    "doctor_assistant": patient.doctor_assistant   # optional
}
patient_data["emergency_contact"] = json.dumps(staff_data)
# Stored as JSON string in emergency_contact column
```

### Camera Manager
```python
class CameraManager:
    # Background thread: cv2.VideoCapture(0, cv2.CAP_DSHOW)
    # Captures at 30fps, resizes to 480×360, encodes JPEG quality 72
    # /snapshot: reads latest JPEG from memory (< 10ms response)
```

### WebSocket Events (sent to all clients)
- `alarm_triggered` — patient alarm with vitals and patient_type
- `vital_update` — periodic vital signs update
- `patient_admitted` / `patient_discharged`
- `nurse_proximity` — BLE proximity update

---

## 10. Database Schema (Supabase PostgreSQL)

**Driver:** `asyncpg` with connection pool (min=5, max=50)

### Table: `patients`
| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | Auto-increment |
| `name` | VARCHAR(255) | Patient name |
| `age` | INTEGER | Patient age |
| `gender` | VARCHAR(10) | Optional |
| `blood_type` | VARCHAR(5) | Optional |
| `weight` / `height` | FLOAT | Optional |
| `problem` | TEXT | Chief complaint |
| `medical_history` | JSONB | Array of conditions |
| `allergies` | JSONB | Array of allergens |
| `current_medications` | JSONB | Array of `{name, dosage, frequency}` |
| `emergency_contact` | VARCHAR(255) | Plain text OR JSON `{doctor_primary, nurse_assigned, doctor_assistant}` |
| `patient_type` | VARCHAR(20) | GENERAL or CRITICAL |
| `status` | VARCHAR(20) | ACTIVE or DISCHARGED |
| `demo_mode` | BOOLEAN | |
| `demo_scenario` | VARCHAR(50) | NORMAL / MILD_DETERIORATION / CRITICAL_EMERGENCY / FALSE_POSITIVE |
| `hardware_mode` | BOOLEAN | True = real ESP32 sensors |
| `disease` | VARCHAR(255) | Disease profile name |
| `body_strength` | VARCHAR(20) | strong / average / weak |
| `genetic_condition` | VARCHAR(50) | healthy / hypertension_prone / diabetes_prone |
| `admission_time` | TIMESTAMP | Auto-set |
| `discharge_time` | TIMESTAMP | Null when active |

### Table: `vital_logs`
| Column | Type |
|---|---|
| `id` | SERIAL PK |
| `patient_id` | INTEGER FK → patients |
| `heart_rate` | FLOAT |
| `spo2` | FLOAT |
| `temperature` | FLOAT |
| `bp_systolic` | FLOAT |
| `bp_diastolic` | FLOAT |
| `respiratory_rate` | FLOAT |
| `blood_glucose` | FLOAT |
| `timestamp` | TIMESTAMP |

Index: `(patient_id, timestamp DESC)`

### Table: `band_assignment`
| Column | Type |
|---|---|
| `band_id` | VARCHAR(50) |
| `patient_id` | INTEGER FK |
| `assigned_at` | TIMESTAMP |
| `released_at` | TIMESTAMP (NULL = active) |

Unique constraint: `(band_id, patient_id)`  
Index: `band_id WHERE released_at IS NULL`

### Table: `alarm_events`
| Column | Type |
|---|---|
| `patient_id` | INTEGER FK |
| `vitals` | JSONB |
| `alarm_status` | VARCHAR(50) |
| `proximity_alert_sent` | BOOLEAN |
| `nurse_in_proximity` | BOOLEAN |
| `timestamp` | TIMESTAMP |

Index: `(patient_id, timestamp DESC)`

### Auto-cleanup
On every backend restart, stale `ACTIVE` patients from previous sessions are automatically discharged and bands released.

---

## 11. Web Frontend (React + Vite)

**Directory:** `frontend_new/`  
**Port:** 3000  
**Stack:** React 18, Vite, Zustand (state), Zod (validation), Tailwind CSS

### Key Pages / Components

| Component | Purpose |
|---|---|
| `AdmitPatient.jsx` | Admit form — selects ward type, disease, patient info |
| `PatientDashboard` | Live vitals, alarm history, discharge button |
| `GeneralWard` | General ward patient list with alarm status |
| `CriticalWard` | Critical ward patient list (BAND_ prefix only) |

### Admit Patient Form — Staff Assignment Validation
When `patient_type === 'CRITICAL'` is selected:
- Animated red-bordered "Staff Assignment" section slides in
- **Required fields:** Primary Doctor name, Assigned Nurse name
- **Optional:** Assistant Doctor name
- Zod schema with `superRefine()`:
```javascript
.superRefine((data, ctx) => {
  if (data.patient_type === 'CRITICAL') {
    if (!data.doctor_primary)  // add issue: required
    if (!data.nurse_assigned)  // add issue: required
  }
})
```

### Network Configuration
Frontend auto-reads backend IP from `NetworkPreferences` (editable in settings). Supports switching between `localhost` and LAN IP for mobile access.

---

## 12. Mobile App (Android Kotlin)

**Directory:** `mobile_app/NurseAlarmApp/`  
**Min SDK:** Android 8.0 (API 26)  
**Language:** Kotlin with Coroutines + lifecycleScope

### Screens

| Screen / Activity | Purpose |
|---|---|
| `MainActivity` | Navigation drawer, ward section routing |
| `GeneralWardFragment` | General ward patient list from WebSocket |
| `CriticalPatientDetailActivity` | Critical patient full detail |
| `AdmitPatientActivity` (via frontend) | — |

### General Ward Flow
```
WebSocket /ws
    │
    ├─ GeneralWardEvent.AlarmTriggered (patient_type=GENERAL)
    │       └─ GeneralWardManager → GeneralAdapter → RecyclerView row
    │
    └─ GeneralWardEvent.AlarmTriggered (patient_type=CRITICAL)
            └─ Guard: return@runOnUiThread (not shown in General list)
```

### Critical Ward Flow
```
MainActivity "Critical Ward" nav item selected
    │
    ├─ GET /api/patients/admitted?patient_type=CRITICAL
    │       └─ criticalAdapter → Critical section RecyclerView
    │               Card: "🔴 ICU Ward • Critical Room 1 | {problem}"
    │
    ├─ startCriticalAlertPolling() — every 15s:
    │       ├─ GET /api/patient/active
    │       ├─ GET /api/patient/{id}/vitals/latest
    │       ├─ Check thresholds (HR>100, SpO2<92, Temp>38, BP_sys>140)
    │       └─ TextToSpeech.speak() if cooldown 30s passed
    │
    └─ Click patient card → CriticalPatientDetailActivity
```

### CriticalPatientDetailActivity

**Features:**
1. **Live Camera Feed** — Native `ImageView`, JPEG polling every 330ms (~3fps)
   - OpenCV backend serves `/snapshot`; native Bitmap decoding, no WebView
2. **Live Vitals** — Polls `/api/patient/{id}/vitals/latest` every 3s
   - 6 vitals displayed: HR, SpO2, BP, Temp, RR, Glucose
   - Abnormal values highlighted red
3. **Alert Banner** — Red banner with abnormal vital list
4. **TTS Voice Alert** — Speaks alert text, 30s cooldown between announcements
5. **Staff Card** — Shows assigned doctor, nurse, assistant (parsed from `emergency_contact` JSON)
6. **Attended Log** — "Mark Attended" button timestamps each nurse visit; persisted to `SharedPreferences` by patient band ID; survives back navigation and app restart

### TTS Alert Thresholds (in-app)
| Vital | Alert Condition |
|---|---|
| Heart Rate | > 100 bpm OR < 50 bpm |
| SpO2 | < 92% |
| Temperature | > 38.0 °C |
| BP Systolic | > 140 mmHg |

### Attended Log Persistence
```kotlin
// Key: "ts_{bandId}" in SharedPreferences "attended_log"
// Format: newline-separated timestamps "dd MMM yyyy  HH:mm:ss"
// Load on onCreate, save on every tap
getSharedPreferences("attended_log", MODE_PRIVATE)
    .getString("ts_BAND_01", "")
```

### Network Preferences
```kotlin
// NetworkPreferences.getInstance(context)
// Stores backend IP in SharedPreferences
// All HTTP calls use: "$baseUrl/api/..."
```

### Key Kotlin Dependencies
- `kotlinx.coroutines` — all async networking
- `com.google.gson` — JSON parsing
- `TextToSpeech` — voice alerts
- `android.speech.tts` — TTS engine

---

## 13. Network & Configuration

### Auto IP Detection
```python
# config.py
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))   # connect to Google DNS (no data sent)
LOCAL_IP = s.getsockname()[0]  # e.g. 10.15.78.101
```

### Zeroconf (mDNS) — Optional Service Discovery
```python
# Backend advertises itself as "_patient-monitor._tcp.local."
# Mobile app can discover backend on LAN without manual IP entry
# Falls back gracefully if zeroconf library not installed
```

### Environment Variables (`.env`)
```
DATABASE_URL=postgresql://...@supabase.io:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
BAND_ID=BAND_01
BLE_PROXIMITY_THRESHOLD_RSSI=-70
```

---

## 14. What Was Achieved

### Core System
- ✅ Real-time patient monitoring with 6 vital parameters
- ✅ Dual operating modes: hardware (ESP32 sensors) and simulation (AI-driven)
- ✅ Two ward types with separate ML models and alarm policies
- ✅ Only one patient active at a time (BAND_01 enforcement)
- ✅ Auto-discharge stale patients on backend restart

### Machine Learning
- ✅ Full NEWS2 implementation per RCP 2017 standard
- ✅ Personalised adjustment layer (disease + medication + age)
- ✅ Random Forest classifiers trained on 8,000 synthetic MIMIC-grounded samples each
- ✅ Vital estimator regressing 4 unmeasured vitals from 3 sensor inputs
- ✅ Medication-aware training — same vitals score differently if patient is on relevant drug
- ✅ Age-based risk amplification (elderly patients escalated faster)

### Backend
- ✅ Full async FastAPI with asyncpg connection pool
- ✅ Real-time WebSocket broadcasts to all connected clients
- ✅ Background OpenCV camera thread with instant JPEG snapshot endpoint
- ✅ Disease profile system with 12+ diseases across both wards
- ✅ Demo mode with controlled vital tampering scenarios for presentations
- ✅ Alarm history logging to database
- ✅ Nurse proximity tracking (BLE RSSI-based)
- ✅ Auto IP detection + Zeroconf LAN service advertising

### Web Frontend
- ✅ Live patient dashboard with real-time vitals
- ✅ General and Critical ward views
- ✅ Admit patient with full medical profile, disease selection, staff assignment
- ✅ Zod schema validation with animated staff section for CRITICAL admissions

### Mobile App
- ✅ WebSocket-driven General Ward live alarm list
- ✅ CRITICAL vs GENERAL alarm routing (CRITICAL alarms excluded from General list)
- ✅ Critical Ward section fetching admitted CRITICAL patients from backend
- ✅ Full Critical patient detail screen: camera, vitals, alerts
- ✅ Pre-click TTS voice alerts from list view (15s polling)
- ✅ Staff assignment display (doctor + nurse parsed from emergency_contact)
- ✅ Mark Attended log with persistent timestamps (SharedPreferences)
- ✅ Native JPEG camera polling (no WebView, ~3fps, <10ms latency from backend)

---

## Running the System

### Start Backend
```powershell
cd backend
$env:PYTHONUTF8="1"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend
```powershell
cd frontend_new
npx vite --host --port 3000
```

### Train ML Models (first time only)
```powershell
cd ML
python train_general.py       # → general_model.pkl
python train_critical.py      # → critical_model.pkl
python train_vital_estimator.py  # → vital_estimator.pkl (move to backend/)
```

### Build Android APK
```powershell
cd mobile_app/NurseAlarmApp
.\gradlew installDebug
```

---

*System IP at last run: `10.15.78.101` | Backend port: `8000` | Frontend port: `3000`*
