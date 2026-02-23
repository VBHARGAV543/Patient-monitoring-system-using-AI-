# Patient Monitoring System Using AI

A real-time, AI-powered hospital patient monitoring system with a **FastAPI backend**, **React web frontend**, and **Android Kotlin mobile app** for nurses. Supports hardware mode (real ESP32 sensors) and simulation mode (AI-driven synthetic vitals) with a full ML pipeline for intelligent alarm classification.

---

## System Overview

```
ESP32 (HR + SpO2 + Temp)
         │
         ▼
  FastAPI Backend  (Port 8000)
  ├─ ML Alarm Classifier (Random Forest)
  ├─ NEWS2 Scoring Engine
  ├─ Disease Profile System
  ├─ Vital Estimator (Hardware Mode)
  ├─ OpenCV Camera Stream
  ├─ WebSocket Real-time Events
  └─ Supabase PostgreSQL
         │
         ├──── React Frontend (Port 3000)
         └──── Android Nurse App (Kotlin)
```

---

## Features

### Backend
- Real-time vital signs monitoring (HR, SpO2, BP, Temperature, RR, Glucose)
- **NEWS2 scoring** — National Early Warning Score 2 (RCP 2017 standard)
- **Random Forest ML classifiers** — separate models for General and Critical wards, trained on 8,000 synthetic MIMIC-grounded samples each
- **Personalised alarm logic** — same vitals score differently depending on disease, active medications, and patient age
- **Vital estimator** — when using hardware (only 3 real sensors), ML regression estimates the 4 unmeasured vitals
- **Disease profile system** — 12+ diseases with realistic medication effects
- **OpenCV camera stream** — background thread captures webcam; instant JPEG snapshot endpoint (<10 ms)
- WebSocket real-time broadcasts to all connected clients
- Automatic discharge of stale patients on server restart
- Demo mode with controlled vital tampering scenarios (Normal / Mild / Critical / False Positive)

### Web Frontend (React + Vite)
- Admit patient with full medical profile, disease, ward type
- Animated staff assignment section (required for Critical ward — validates Primary Doctor + Nurse)
- Live patient dashboard with vitals and alarm history
- General and Critical ward views

### Android Nurse App (Kotlin)
- WebSocket-driven General Ward live alarm list
- Critical Ward section — fetches admitted CRITICAL patients from backend
- Critical patient detail screen: live camera, 6 vitals, alert banner
- **Pre-click TTS voice alerts** — speaks alarm before nurse opens patient card (polls every 15s)
- **Staff display** — shows assigned doctor and nurse on patient detail screen
- **Mark Attended log** — timestamps each nurse visit, persisted across sessions (SharedPreferences)
- CRITICAL alarms correctly excluded from General Ward list

---

## Hardware (Optional)

| Component | Role | Interface |
|---|---|---|
| ESP32 | Main MCU — sends sensor readings over WiFi | HTTP POST JSON |
| MAX30102 | Heart Rate + SpO2 | I2C |
| DS18B20 | Body temperature (°C) | OneWire |

In hardware mode, only HR, SpO2, and Temp are real. The backend ML regressor estimates BP, RR, and Glucose from these 3 inputs.

---

## ML Pipeline

### NEWS2 Algorithm
**Source:** https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2

Scores 6 vital parameters (RR, SpO2, BP_sys, HR, Consciousness, Temp) on a 0–20 scale:
- **0–4** → LOW (Safe)
- **5–6** → MEDIUM (Warning)
- **≥7** → HIGH (Critical)

### Personalised Adjustments
The system escalates alarms beyond the raw NEWS2 score when treatment is failing:
- Hypertension patient on BP medication but BP still > 155 mmHg → escalate
- Diabetic on insulin but glucose > 220 mg/dL → escalate
- Asthma patient on bronchodilator but SpO2 < 90% → critical
- Pneumonia patient on antibiotics but fever > 39.5°C → escalate
- Age ≥ 70 with elevated score → additional risk amplification

### ML Models

| Model | Ward | Features | Algorithm | Samples |
|---|---|---|---|---|
| `general_model.pkl` | General | 19 | RandomForestClassifier | 8,000 |
| `critical_model.pkl` | Critical | 20 | RandomForestClassifier | 8,000 |
| `vital_estimator.pkl` | Both | 17 | RandomForestRegressor ×4 | 16,000 |

Output labels: **0 = Safe**, **1 = Warning**, **2 = Critical**

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app (1487 lines), all endpoints
│   ├── ml_predictor.py      # Loads .pkl models, builds feature vectors
│   ├── alarm_policy.py      # Alarm suppression logic per ward type
│   ├── disease_profiles.py  # 12+ disease definitions with medications
│   ├── vital_estimator.py   # Hardware-mode vital regression
│   ├── database.py          # asyncpg Supabase layer
│   ├── schemas.py           # Pydantic request/response models
│   └── requirements.txt
│
├── ML/
│   ├── news2.py             # Full NEWS2 scorer + personalised adjustment
│   ├── simulate_data_general.py   # MIMIC-grounded training data generator
│   ├── simulate_data_critical.py  # Critical ward training data generator
│   ├── train_general.py     # Train general ward RF classifier
│   ├── train_critical.py    # Train critical ward RF classifier
│   └── train_vital_estimator.py   # Train vital regression models
│
├── frontend_new/            # React + Vite web frontend (Port 3000)
│   └── src/
│       ├── pages/
│       ├── components/
│       └── services/
│
├── mobile_app/
│   └── NurseAlarmApp/       # Android Kotlin app
│       └── app/src/main/java/com/example/nursealarmapp/
│
└── PROJECT_OVERVIEW.md      # Full technical documentation
```

---

## Quick Start

### 1. Backend

```powershell
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and fill in DATABASE_URL (Supabase)
$env:PYTHONUTF8="1"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

### 2. Train ML Models (first time only)

```powershell
cd ML
python train_general.py          # → general_model.pkl
python train_critical.py         # → critical_model.pkl
python train_vital_estimator.py  # → vital_estimator.pkl  (copy to backend/)
```

### 3. Frontend

```powershell
cd frontend_new
npm install
npx vite --host --port 3000
```

### 4. Android App

```powershell
cd mobile_app/NurseAlarmApp
.\gradlew installDebug
```

Set the backend IP in the app's Network Settings to match your machine's LAN IP.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/patient/admit` | Admit new patient |
| `GET` | `/api/patient/active` | Get currently active patient |
| `GET` | `/api/patients/admitted` | List admitted patients (`?patient_type=CRITICAL`) |
| `POST` | `/api/patient/{id}/discharge` | Discharge a patient |
| `GET` | `/api/patient/{id}/vitals/latest` | Latest vital signs |
| `POST` | `/api/sensor/data` | Receive ESP32 sensor data |
| `GET` | `/snapshot` | Latest camera JPEG |
| `GET` | `/stream` | MJPEG camera stream |
| `WS` | `/ws` | Real-time WebSocket events |

---

## Environment Variables

Create a `.env` file in `backend/`:

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_key
BAND_ID=BAND_01
```

---

## Full Technical Documentation

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for complete details including all formulas, feature vectors, disease databases, alarm thresholds, database schema, and implementation notes.

---

## License

See [LICENSE](LICENSE) for details.
