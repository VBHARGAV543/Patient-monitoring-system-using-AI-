from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, HTMLResponse
from schemas import (
    CriticalPatientData, GeneralPatientData, PredictRequest, RealSensorData,
    PatientAdmit, PatientResponse, AlarmEventResponse,
    NurseRegister, NurseProximityUpdate, NurseSessionResponse,
    VitalSignsLog, MockMLPrediction
)
import database
import alarm_policy
import mock_data
import ml_predictor
import disease_profiles
import vital_estimator
import config
import os
import json
import uuid
import asyncio
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import cv2
import socket
try:
    from zeroconf import Zeroconf, ServiceInfo
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False

# ML models are loaded inside ml_predictor.py (NEWS2 + Random Forest pipeline)


# ========== Persistent Camera Manager ==========
class CameraManager:
    """
    Runs a background thread that continuously captures frames from the webcam.
    /snapshot just reads the latest stored JPEG — no per-request camera I/O,
    so responses are instant (< 10 ms) after the first warm-up.
    """
    def __init__(self):
        self._latest_jpeg: Optional[bytes] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print("[Camera] Background capture thread started")

    def _capture_loop(self):
        # CAP_DSHOW = DirectShow backend — much faster init and frame rate on Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        # Warm-up: discard first few frames (often black on Windows)
        for _ in range(5):
            cap.read()
        print("[Camera] Webcam ready, capturing frames...")
        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            if ok:
                with self._lock:
                    self._latest_jpeg = buf.tobytes()
        cap.release()
        print("[Camera] Webcam released")

    def get_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def stop(self):
        self._running = False


camera_mgr = CameraManager()


# Lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_available = False
    try:
        await database.init_db()
        db_available = True
        # Always clean up stale ACTIVE patients from previous server session
        cleaned = await database.auto_discharge_on_restart()
        if cleaned:
            print(f"[STARTUP] Auto-discharged {cleaned} stale patient(s) from previous session -- band is now free")
        else:
            print("[STARTUP] No stale patients found -- band is clean")
    except ValueError as e:
        print(f"\n⚠️  DATABASE_URL not set - running in mock mode")
        print(f"⚠️  Patient data will be simulated (no real DB connection)")
        print(f"⚠️  To enable DB: create backend/.env with DATABASE_URL=postgresql://...\n")
    except Exception as e:
        print(f"\n⚠️  Database connection failed: {e}")
        print(f"⚠️  Running in mock mode\n")
    
    # Reload patient profiles for any active patients
    if db_available:
        try:
            patient = await database.get_active_patient()
            if patient and patient.get('disease'):
                print(f"🔄 Reloading profile for active patient: {patient['name']} (ID: {patient['id']})")
                ward_type = "critical" if patient['patient_type'] == "CRITICAL" else "general"
                profile = disease_profiles.generate_patient_profile(
                    age=patient['age'],
                    gender=patient['gender'],
                    disease=patient['disease'],
                    ward_type=ward_type,
                    body_strength=patient.get('body_strength') or "average",
                    genetic_condition=patient.get('genetic_condition') or "healthy",
                    allergies=patient.get('allergies') or []
                )
                patient_profiles[patient['id']] = profile
                patient_admission_times[patient['id']] = patient['admission_time']
                print(f"✅ Profile reloaded for patient {patient['id']}")
        except Exception as e:
            print(f"⚠️ Error reloading patient profiles: {e}")
    
    # Start background vital signs simulation
    vital_task = asyncio.create_task(simulate_vitals_background())

    # Start persistent camera background capture thread
    camera_mgr.start()

    # Advertise via mDNS so ESP32 can find us as 'hospital.local'
    zc = None
    zc_info = None
    if ZEROCONF_AVAILABLE:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            zc = Zeroconf()
            zc_info = ServiceInfo(
                "_http._tcp.local.",
                "hospital._http._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=8000,
                properties={"path": "/"},
                server="hospital.local.",
            )
            zc.register_service(zc_info)
            print(f"[mDNS] Advertising as hospital.local -> {local_ip}:8000")
        except Exception as e:
            print(f"[mDNS] Failed to start: {e}")

    yield

    # Shutdown
    vital_task.cancel()
    camera_mgr.stop()
    if zc and zc_info:
        try:
            await asyncio.to_thread(zc.unregister_service, zc_info)
            await asyncio.to_thread(zc.close)
            print("[mDNS] Service unregistered")
        except Exception as e:
            print(f"[mDNS] Shutdown warning (non-fatal): {e}")
    if db_available:
        await database.close_db()


app = FastAPI(title="Hospital Alarm Fatigue Monitoring API", lifespan=lifespan)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection managers
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.nurse_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def connect_nurse(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.nurse_connections[session_id] = websocket

    def disconnect_nurse(self, session_id: str):
        if session_id in self.nurse_connections:
            del self.nurse_connections[session_id]

    async def broadcast(self, message: dict):
        """Broadcast to main dashboard connections, auto-removing dead ones"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for conn in dead_connections:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    async def send_to_nurse(self, session_id: str, message: dict):
        """Send message to specific nurse session"""
        if session_id in self.nurse_connections:
            try:
                await self.nurse_connections[session_id].send_text(json.dumps(message))
            except:
                pass


manager = ConnectionManager()

# Global vital signs simulators for active patients
vital_simulators: Dict[int, mock_data.VitalSignsSimulator] = {}
patient_profiles: Dict[int, disease_profiles.PatientProfile] = {}
patient_admission_times: Dict[int, datetime] = {}

# Background task for simulating vital signs
async def simulate_vitals_background():
    """Background task that continuously generates vital signs for active patients"""
    print("🚀 Starting vital signs background task...")
    while True:
        try:
            # Skip DB-dependent work if no database connection
            if database.pool is None:
                await asyncio.sleep(5)
                continue

            # Get active patient
            patient = await database.get_active_patient()
            
            if patient:
                print(f"✅ Active patient found: {patient['name']} (ID: {patient['id']}, Type: {patient['patient_type']})")
                patient_id = patient['id']

                # Hardware mode: vitals come ONLY from the real sensor endpoint.
                # Skip simulation entirely so we don't overwrite real readings.
                if patient.get('hardware_mode', False):
                    print("⏸️ Hardware mode active -- skipping simulation, waiting for real sensor data...")
                    await asyncio.sleep(8)
                    continue

                # Use disease profile system if available
                if patient_id in patient_profiles:
                    print(f"✅ Using disease profile for patient {patient_id}")
                    profile = patient_profiles[patient_id]
                    admission_time = patient_admission_times[patient_id]
                    hours_since_admission = (datetime.now() - admission_time).total_seconds() / 3600
                    
                    # Calculate current vitals based on disease profile
                    vitals_dict = disease_profiles.calculate_current_vitals(profile, hours_since_admission)
                    
                    # Format vitals for system (both formats for compatibility)
                    vitals = {
                        'HR': int(vitals_dict['HR']),
                        'SpO2': int(vitals_dict['SpO2']),
                        'Temp': round(vitals_dict['Temp'], 1),
                        'BP_sys': int(vitals_dict['BP_sys']),
                        'BP_dia': int(vitals_dict['BP_dia']),
                        'RR': int(vitals_dict['RR']),
                        'Glucose': int(vitals_dict['Glucose'])
                    }
                    
                else:
                    # Fall back to old simulator system
                    # Create simulator if doesn't exist
                    if patient_id not in vital_simulators:
                        vital_simulators[patient_id] = mock_data.VitalSignsSimulator(
                            patient_id=patient_id,
                            patient_type=patient['patient_type'],
                            demo_scenario=patient.get('demo_scenario')
                        )
                    
                    # Generate new vitals
                    vitals = vital_simulators[patient_id].generate_next_reading()
                
                # Log to database (map keys to database column names)
                await database.log_vital_signs(
                    patient_id=patient_id,
                    heart_rate=int(vitals['HR']),
                    spo2=int(vitals['SpO2']),
                    temperature=float(vitals['Temp']),
                    bp_systolic=int(vitals['BP_sys']),
                    bp_diastolic=int(vitals['BP_dia']),
                    respiratory_rate=int(vitals['RR']),
                    blood_glucose=int(vitals['Glucose'])
                )
                
                # Run ML prediction on vitals (Real RF — NEWS2 + patient profile)
                ml_prediction = ml_predictor.predict_alarm(
                    vitals=vitals,
                    patient_type=patient['patient_type'],
                    patient_profile=patient_profiles.get(patient_id)
                )
                
                print(f"📊 Vitals generated: HR={vitals['HR']}, SpO2={vitals['SpO2']}, Temp={vitals['Temp']}, Prediction={ml_prediction['prediction']}")
                
                # Prepare vital update message with patient_type
                vital_update_msg = {
                    "event": "vital_signs_update",
                    "patient_id": patient_id,
                    "patient_name": patient['name'],
                    "patient_type": patient['patient_type'],
                    "vitals": vitals,
                    "ml_prediction": ml_prediction,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Broadcast to dashboard
                await manager.broadcast(vital_update_msg)
                print(f"📡 Broadcasted vital update to {len(manager.active_connections)} dashboard connections")
                
                # Broadcast to all connected nurses
                for session_id in list(manager.nurse_connections.keys()):
                    try:
                        await manager.send_to_nurse(session_id, vital_update_msg)
                        print(f"📡 Sent vital update to nurse {session_id}")
                    except Exception as e:
                        print(f"Failed to send to nurse {session_id}: {e}")
                
                # Check if alarm should trigger
                if ml_prediction['prediction'] == 1:
                    print(f"🚨 ALARM TRIGGERED - Patient: {patient['name']}, Type: {patient['patient_type']}")
                    
                    alarm_msg = {
                        "event": "alarm_triggered",
                        "patient_id": patient_id,
                        "patient_name": patient['name'],
                        "patient_type": patient['patient_type'],
                        "vitals": vitals,
                        "prediction": ml_prediction,
                        "timestamp": datetime.now().isoformat(),
                        "band_id": patient.get('band_id', 'UNKNOWN'),
                        "notification_title": "🚨 Proximity Alert",
                        "notification_message": f"You are near {patient['name']} - Patient alarm triggered due to concerning vitals"
                    }
                    
                    # Broadcast to dashboard
                    await manager.broadcast(alarm_msg)
                    print(f"📡 Broadcasted alarm to dashboard")
                    
                    # For GENERAL ward, check proximity before sending to nurses
                    if patient['patient_type'] == 'GENERAL':
                        # Get patient's band_id
                        patient_band_id = patient.get('band_id', 'UNKNOWN')
                        print(f"🔍 Checking nurse proximity for {patient_band_id}...")
                        
                        # Check which nurses are in proximity to this patient's band
                        for session_id in list(manager.nurse_connections.keys()):
                            # Get nurse proximity data from database
                            nurse_session = await database.get_nurse_session(session_id)
                            if nurse_session:
                                nearby_devices = nurse_session.get('ble_devices_nearby', [])
                                print(f"   Nurse {session_id[:8]}... nearby devices: {nearby_devices}")
                                
                                if patient_band_id in nearby_devices:
                                    try:
                                        await manager.send_to_nurse(session_id, alarm_msg)
                                        print(f"🔔 ALARM SENT to nurse {session_id[:8]}... (in proximity to {patient_band_id})")
                                        print(f"   📦 Alarm message: {json.dumps(alarm_msg, default=str)}")
                                    except Exception as e:
                                        print(f"Failed to send alarm to nurse {session_id}: {e}")
                                else:
                                    print(f"   Nurse {session_id[:8]}... NOT in proximity, skipping alarm")
                    else:
                        # For CRITICAL ward, send to all nurses
                        print(f"📡 Broadcasting alarm to all {len(manager.nurse_connections)} nurses (CRITICAL ward)")
                        for session_id in list(manager.nurse_connections.keys()):
                            try:
                                await manager.send_to_nurse(session_id, alarm_msg)
                                print(f"🔔 Alarm sent to nurse {session_id[:8]}...")
                            except Exception as e:
                                print(f"Failed to send alarm to nurse {session_id}: {e}")
            else:
                print("⏸️ No active patient found, waiting...")
            
            # Wait 8 seconds before next reading
            await asyncio.sleep(8)
            
        except Exception as e:
            print(f"❌ Error in vital signs simulation: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(8)


# ========== DISEASE SELECTION APIs ==========

@app.get("/api/diseases/{ward_type}")
async def get_diseases(ward_type: str) -> List[str]:
    """Get available diseases for a ward type"""
    if ward_type == "critical":
        return list(disease_profiles.CRITICAL_WARD_DISEASES.keys())
    elif ward_type == "general":
        return list(disease_profiles.GENERAL_WARD_DISEASES.keys())
    else:
        raise HTTPException(status_code=400, detail="Invalid ward_type")

@app.get("/api/diseases/{ward_type}/{disease_name}")
async def get_disease_info(ward_type: str, disease_name: str):
    """Get detailed information about a disease"""
    disease_db = disease_profiles.CRITICAL_WARD_DISEASES if ward_type == "critical" else disease_profiles.GENERAL_WARD_DISEASES
    
    if disease_name not in disease_db:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    return disease_db[disease_name]


# ========== PATIENT LIFECYCLE APIs ==========

@app.post("/api/patient/admit", response_model=PatientResponse)
async def admit_patient(patient: PatientAdmit):
    """
    Admit a new patient and bind BAND_01
    Auto-generates realistic medical profile based on disease selection
    """
    try:
        # Check if band is available
        if not await database.is_band_available():
            raise HTTPException(
                status_code=400,
                detail="BAND_01 is currently assigned to another patient. Please discharge the current patient first."
            )
        
        # Initialize patient data
        patient_data = {
            "name": patient.name,
            "age": patient.age,
            "problem": patient.problem,
            "patient_type": patient.patient_type,
            "demo_mode": patient.demo_mode,
            "demo_scenario": patient.demo_scenario,
            "hardware_mode": patient.hardware_mode,
        }

        # For Critical ward: pack staff assignment into emergency_contact as JSON
        if patient.patient_type == "CRITICAL" and (patient.doctor_primary or patient.nurse_assigned):
            import json as _json
            staff_data = {}
            if patient.doctor_primary:  staff_data["doctor_primary"]  = patient.doctor_primary
            if patient.nurse_assigned:  staff_data["nurse_assigned"]  = patient.nurse_assigned
            if patient.doctor_assistant: staff_data["doctor_assistant"] = patient.doctor_assistant
            patient_data["emergency_contact"] = _json.dumps(staff_data)
            print(f"👨‍⚕️ Critical ward staff assigned: {staff_data}")
        
        # Use disease profile system if disease is specified
        if patient.disease:
            try:
                # Generate realistic patient profile based on disease
                ward_type = "critical" if patient.patient_type == "CRITICAL" else "general"
                profile = disease_profiles.generate_patient_profile(
                    age=patient.age,
                    gender=patient.gender or "Male",
                    disease=patient.disease,
                    ward_type=ward_type,
                    body_strength=patient.body_strength or "average",
                    genetic_condition=patient.genetic_condition or "healthy",
                    allergies=patient.allergies or []
                )
                
                # Store profile for vital simulation
                # We'll use patient_id after creation, stored in patient_profiles dict
                
                # Generate mock profile for missing demographic data
                mock_profile = mock_data.generate_patient_profile(patient.patient_type)
                
                # Clean medications - remove vitals_effect before storing in DB
                clean_medications = [
                    {
                        "name": med["name"],
                        "dosage": med["dosage"],
                        "frequency": med["frequency"]
                    }
                    for med in profile.medications
                ]
                
                # Use profile data
                patient_data.update({
                    "gender": profile.gender,
                    "blood_type": patient.blood_type or mock_profile.get("blood_type"),
                    "weight": patient.weight or mock_profile.get("weight"),
                    "height": patient.height or mock_profile.get("height"),
                    "medical_history": [profile.disease] + (patient.medical_history or []),
                    "allergies": profile.allergies,
                    "current_medications": clean_medications,
                    "emergency_contact": patient_data.get("emergency_contact") or patient.emergency_contact or mock_profile.get("emergency_contact"),
                    "emergency_phone": patient.emergency_phone or mock_profile.get("emergency_phone"),
                    "disease": profile.disease,
                    "body_strength": profile.body_strength,
                    "genetic_condition": profile.genetic_condition
                })
                
                print(f"✅ Disease profile created: {profile.disease} for {ward_type} ward")
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        # Generate mock medical data if in demo mode (fallback for old system)
        elif patient.demo_mode:
            mock_profile = mock_data.generate_patient_profile(patient.patient_type)
            
            # Merge mock data with admission data
            patient_data.update({
                "gender": patient.gender or mock_profile.get("gender"),
                "blood_type": patient.blood_type or mock_profile.get("blood_type"),
                "weight": patient.weight or mock_profile.get("weight"),
                "height": patient.height or mock_profile.get("height"),
                "medical_history": patient.medical_history or mock_profile.get("medical_history"),
                "allergies": patient.allergies or mock_profile.get("allergies"),
                "current_medications": patient.current_medications or mock_profile.get("current_medications"),
                "emergency_contact": patient_data.get("emergency_contact") or patient.emergency_contact or mock_profile.get("emergency_contact"),
                "emergency_phone": patient.emergency_phone or mock_profile.get("emergency_phone"),
                "disease": patient.disease,
                "body_strength": patient.body_strength,
                "genetic_condition": patient.genetic_condition
            })
        else:
            # Use provided data only
            patient_data.update({
                "gender": patient.gender,
                "blood_type": patient.blood_type,
                "weight": patient.weight,
                "height": patient.height,
                "medical_history": patient.medical_history,
                "allergies": patient.allergies,
                "current_medications": patient.current_medications,
                "emergency_contact": patient.emergency_contact,
                "emergency_phone": patient.emergency_phone,
                "disease": patient.disease,
                "body_strength": patient.body_strength,
                "genetic_condition": patient.genetic_condition
            })
        
        # Create patient record
        patient_record = await database.create_patient(**patient_data)
        
        # Store profile if using disease system
        if patient.disease:
            ward_type = "critical" if patient.patient_type == "CRITICAL" else "general"
            profile = disease_profiles.generate_patient_profile(
                age=patient.age,
                gender=patient_record['gender'],
                disease=patient.disease,
                ward_type=ward_type,
                body_strength=patient_record['body_strength'] or "average",
                genetic_condition=patient_record['genetic_condition'] or "healthy",
                allergies=patient_record['allergies'] or []
            )
            patient_profiles[patient_record['id']] = profile
            patient_admission_times[patient_record['id']] = datetime.now()
        
        # Assign band to patient
        band_assignment = await database.assign_band_to_patient(patient_record['id'])
        
        # Initialize vital signs simulator (for old system compatibility)
        vital_simulators[patient_record['id']] = mock_data.VitalSignsSimulator(
            patient_id=patient_record['id'],
            patient_type=patient_record['patient_type'],
            demo_scenario=patient_record.get('demo_scenario')
        )
        
        # Combine patient and band info
        response = PatientResponse(
            **patient_record,
            band_id=band_assignment['band_id'],
            assigned_at=band_assignment['assigned_at']
        )
        
        # Broadcast admission event to dashboard
        await manager.broadcast({
            "event": "patient_admitted",
            "patient": response.dict()
        })
        
        print(f"✅ Patient admitted: {patient.name} (ID: {patient_record['id']}) - BAND_01 assigned")
        if patient.disease:
            print(f"   Disease: {patient.disease}, Profile-based vitals enabled")
            print(f"🎭 Mock medical profile generated for {patient.name}")
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to admit patient: {str(e)}")


@app.post("/api/band/reset")
async def reset_band():
    """
    Force-release the band if it's stuck as occupied.
    Use this when BAND_01 shows as occupied but no patient is active.
    Also discharges any lingering ACTIVE patients.
    """
    if database.pool is None:
        return {"released": 0, "message": "No database connection (mock mode)"}
    count = await database.force_release_band()
    # Also discharge any leftover ACTIVE patients so the band is truly free
    discharged = await database.auto_discharge_on_restart()
    available = await database.is_band_available()
    total = count + discharged
    print(f"[BAND RESET] Released {count} assignment(s), discharged {discharged} stale patient(s). Available={available}")
    return {
        "released": total,
        "band_id": "BAND_01",
        "now_available": available,
        "message": f"Released {count} assignment(s) and discharged {discharged} stale patient(s). Band is now {'available' if available else 'still occupied'}."
    }


@app.post("/api/patient/discharge/{patient_id}")
async def discharge_patient(patient_id: int):
    """
    Discharge a patient and release BAND_01
    """
    try:
        # Get patient info before discharge (raw data, no validation)
        patient = await database.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if patient.get('status') == 'DISCHARGED':
            raise HTTPException(status_code=400, detail="Patient already discharged")
        
        # Remove vital simulator
        if patient_id in vital_simulators:
            del vital_simulators[patient_id]
        
        # Discharge patient and release band
        success = await database.discharge_patient(patient_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to discharge patient")
        
        # Broadcast discharge event
        await manager.broadcast({
            "event": "patient_discharged",
            "patient_id": patient_id,
            "name": patient['name']
        })
        
        print(f"✅ Patient discharged: {patient['name']} (ID: {patient_id}) - BAND_01 released")
        
        return {
            "status": "success",
            "message": f"Patient {patient['name']} discharged successfully",
            "patient_id": patient_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discharge patient: {str(e)}")


@app.get("/api/patient/active", response_model=Optional[PatientResponse])
async def get_active_patient():
    """
    Get currently active patient with band assignment
    """
    if database.pool is None:
        return None  # No DB - no active patient, band is available
    try:
        patient = await database.get_active_patient()
        
        if not patient:
            return None
        
        # Clean medications to remove vitals_effect (backward compatibility)
        if patient.get('current_medications'):
            cleaned_meds = []
            for med in patient['current_medications']:
                if isinstance(med, dict):
                    # Remove vitals_effect if present
                    cleaned_med = {
                        "name": med.get("name", ""),
                        "dosage": med.get("dosage", ""),
                        "frequency": med.get("frequency", "")
                    }
                    cleaned_meds.append(cleaned_med)
            patient['current_medications'] = cleaned_meds
        
        # Debug: print patient data
        print(f"📋 Patient data from DB (cleaned): {patient}")
        
        return PatientResponse(**patient)
        
    except Exception as e:
        print(f"❌ Error in get_active_patient: {str(e)}")
        print(f"❌ Patient data that caused error: {patient if 'patient' in locals() else 'No data'}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch active patient: {str(e)}")


@app.get("/api/patient/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int):
    """
    Get specific patient by ID
    """
    try:
        patient = await database.get_patient_by_id(patient_id)
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse(**patient)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch patient: {str(e)}")


@app.get("/api/patient/{patient_id}/alarm-history", response_model=List[AlarmEventResponse])
async def get_patient_alarm_history(patient_id: int, limit: int = 50):
    """
    Get alarm event history for a patient
    """
    if database.pool is None:
        return []
    try:
        events = await database.get_patient_alarm_history(patient_id, limit)
        return [AlarmEventResponse(**event) for event in events]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alarm history: {str(e)}")


@app.get("/api/patient/{patient_id}/vitals", response_model=List[VitalSignsLog])
async def get_patient_vitals(patient_id: int, limit: int = 100):
    """
    Get vital signs history for a patient
    """
    if database.pool is None:
        return []
    try:
        vitals = await database.get_patient_vital_history(patient_id, limit)
        return [VitalSignsLog(**vital) for vital in vitals]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vital signs: {str(e)}")


@app.get("/api/patient/{patient_id}/vitals/latest")
async def get_patient_latest_vitals(patient_id: int):
    """
    Get most recent vital signs for a patient
    """
    try:
        vitals = await database.get_latest_vitals(patient_id)
        
        if not vitals:
            raise HTTPException(status_code=404, detail="No vital signs found for patient")
        
        return VitalSignsLog(**vitals)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest vitals: {str(e)}")


@app.post("/api/patient/{patient_id}/vitals/simulate")
async def simulate_patient_vitals(patient_id: int, scenario: str = "NORMAL"):
    """
    Manually trigger vital signs simulation for a patient
    Scenario options: NORMAL, MILD_DETERIORATION, CRITICAL_EMERGENCY, FALSE_POSITIVE
    """
    try:
        # Get patient info
        patient = await database.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if patient['status'] != 'ACTIVE':
            raise HTTPException(status_code=400, detail="Can only simulate vitals for active patients")
        
        # Generate mock vitals with specified scenario
        vitals = mock_data.generate_mock_vitals(
            patient_type=patient['patient_type'],
            demo_scenario=scenario
        )
        
        # Log to database (map keys to database column names)
        await database.log_vital_signs(
            patient_id=patient_id,
            heart_rate=int(vitals['HR']),
            spo2=int(vitals['SpO2']),
            temperature=float(vitals['Temp']),
            bp_systolic=int(vitals['BP_sys']),
            bp_diastolic=int(vitals['BP_dia']),
            respiratory_rate=int(vitals['RR']),
            blood_glucose=int(vitals['Glucose'])
        )
        
        # Generate ML prediction
        ml_prediction = mock_data.mock_ml_prediction(vitals, patient['patient_type'])
        
        # Broadcast to dashboard
        await manager.broadcast({
            "event": "vital_signs_update",
            "patient_id": patient_id,
            "patient_name": patient['name'],
            "vitals": vitals,
            "ml_prediction": ml_prediction,
            "scenario": scenario,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "patient_id": patient_id,
            "vitals": vitals,
            "ml_prediction": ml_prediction,
            "scenario": scenario
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate vitals: {str(e)}")


@app.get("/api/patients/admitted")
async def get_admitted_patients(patient_type: Optional[str] = None):
    """
    Get all currently admitted (ACTIVE) patients.
    Optional query param: ?patient_type=GENERAL or CRITICAL
    """
    if database.pool is None:
        return []
    try:
        patients = await database.get_admitted_patients(patient_type)
        return patients
    except Exception as e:
        print(f"❌ Error in get_admitted_patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch admitted patients: {str(e)}")


@app.get("/api/patients/discharged", response_model=List[PatientResponse])
async def get_discharged_patients(limit: Optional[int] = None):
    """
    Get discharged patient history (all records by default, optional limit)
    """
    if database.pool is None:
        return []  # No DB - return empty list in mock mode
    try:
        patients = await database.get_discharged_patients(limit)
        
        # Add band_id and assigned_at as None for discharged patients (band was released)
        for patient in patients:
            if 'band_id' not in patient:
                patient['band_id'] = None
            if 'assigned_at' not in patient:
                patient['assigned_at'] = None
        
        return [PatientResponse(**patient) for patient in patients]
        
    except Exception as e:
        print(f"❌ Error in get_discharged_patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch discharged patients: {str(e)}")


@app.get("/api/patients/statistics")
async def get_patient_statistics():
    """
    Get patient admission/discharge statistics
    """
    if database.pool is None:
        return {"total_admitted": 0, "total_discharged": 0, "total_critical": 0, "total_general": 0}
    try:
        stats = await database.get_patient_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


# ========== NURSE PROXIMITY APIs ==========

@app.post("/api/nurse/register", response_model=NurseSessionResponse)
async def register_nurse(nurse: NurseRegister):
    """
    Register nurse device for proximity monitoring
    """
    try:
        session_id = str(uuid.uuid4())
        print(f"🔵 Registering nurse with session_id: {session_id}, device: {nurse.device_info}")
        
        session = await database.create_nurse_session(session_id, nurse.device_info)
        print(f"✅ Nurse registered successfully: {session}")
        
        return NurseSessionResponse(
            session_id=session['session_id'],
            device_info=session['device_info'],
            registered_at=session['registered_at'],
            last_proximity_update=None,
            ble_devices_nearby=[],
            in_proximity=False
        )
        
    except Exception as e:
        print(f"❌ Nurse registration failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to register nurse: {str(e)}")


@app.post("/api/nurse/proximity")
async def update_nurse_proximity(proximity: NurseProximityUpdate):
    """
    Update nurse proximity with detected BLE devices
    """
    try:
        print(f"🔵 Proximity update - session_id: {proximity.session_id}, devices: {proximity.ble_devices_nearby}")
        
        # Auto-create session if it doesn't exist (handles Android app session_id mismatch)
        success = await database.update_nurse_proximity(proximity.session_id, proximity.ble_devices_nearby)
        if not success:
            print(f"⚠️ Session not found, creating: {proximity.session_id}")
            await database.create_nurse_session(proximity.session_id, "Auto-created from proximity")
            success = await database.update_nurse_proximity(proximity.session_id, proximity.ble_devices_nearby)
        
        return {
            "status": "success",
            "session_id": proximity.session_id,
            "devices_detected": len(proximity.ble_devices_nearby)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update proximity: {str(e)}")


@app.get("/api/nurse/status/{session_id}", response_model=NurseSessionResponse)
async def get_nurse_status(session_id: str):
    """
    Get nurse session status and proximity info
    """
    try:
        session = await database.get_nurse_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Nurse session not found")
        
        # Check if nurse is currently in proximity
        in_proximity = await database.check_nurse_proximity()
        
        return NurseSessionResponse(**session, in_proximity=in_proximity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nurse status: {str(e)}")


# ========== SENSOR DATA & ALARM PROCESSING ==========

@app.post("/api/sensor-data")
async def receive_sensor_data(sensor_data: RealSensorData):
    """
    Main endpoint for ESP32 sensor data
    1. Validates band assignment
    2. Retrieves active patient context
    3. Applies demo tampering if enabled
    4. Runs ML prediction
    5. Evaluates alarm policy with BLE proximity
    6. Logs alarm event
    7. Routes alerts appropriately
    """
    try:
        # Step 1: Get active patient assigned to this band
        patient = await database.get_patient_by_band(sensor_data.band_id)
        
        if not patient:
            raise HTTPException(
                status_code=400,
                detail=f"Band {sensor_data.band_id} is not assigned to any active patient. Please admit a patient first."
            )
        
        # Step 2: Prepare vitals
        # Hardware mode: only HR, SpO2, Temp are real — estimate the rest via ML
        # Simulation mode: full 7-vital simulation is already available, use as-is
        is_hardware_mode = patient.get('hardware_mode', False)

        if is_hardware_mode:
            # Try ML estimator; fall back to safe defaults if pkl is incompatible
            try:
                estimated = vital_estimator.estimate_missing_vitals(
                    HR=sensor_data.HR,
                    SpO2=sensor_data.SpO2,
                    Temp=sensor_data.Temp,
                    age=patient.get('age', 50),
                    patient_type=patient['patient_type'],
                    disease=patient.get('problem', ''),
                )
            except Exception as est_err:
                print(f"[WARN] vital_estimator failed ({est_err}), using safe defaults for estimated fields")
                estimated = {"BP_sys": 120, "BP_dia": 80, "RR": 16, "Glucose": 100}
            vitals = {
                "HR":     sensor_data.HR,          # real -- MAX30102
                "SpO2":   sensor_data.SpO2,        # real -- MAX30102
                "Temp":   sensor_data.Temp,        # real -- DS18B20
                "BP_sys": estimated["BP_sys"],     # (est.) -- regression model
                "BP_dia": estimated["BP_dia"],     # (est.) -- regression model
                "RR":     estimated["RR"],         # (est.) -- regression model
                "Glucose":estimated["Glucose"],    # (est.) -- regression model
                "_estimated_fields": ["BP_sys", "BP_dia", "RR", "Glucose"],
            }
        else:
            vitals = {
                "HR":     sensor_data.HR,
                "SpO2":  sensor_data.SpO2,
                "Temp":  sensor_data.Temp,
                "BP_sys":120,
                "BP_dia":80,
                "RR":    16,
                "Glucose":100,
            }
        
        # Step 3: Apply demo tampering if enabled
        if patient['demo_mode'] and patient['demo_scenario']:
            vitals = alarm_policy.apply_demo_tampering(
                vitals,
                patient['demo_scenario'],
                patient['patient_type']
            )
        
        # Step 4 & 5: Run ML prediction via ml_predictor (handles both RF and NEWS2 fallback)
        patient_profile = patient_profiles.get(patient['id'])
        ml_result = ml_predictor.predict_alarm(
            vitals=vitals,
            patient_type=patient['patient_type'],
            patient_profile=patient_profile
        )
        prediction = ml_result["prediction"]
        
        # Step 6: Check nurse proximity
        nurses_in_proximity = await database.get_nurses_in_proximity(sensor_data.band_id)
        nurse_in_ble_range = len(nurses_in_proximity) > 0
        
        # Step 7: Evaluate alarm policy
        alarm_decision = alarm_policy.evaluate_alarm(
            patient_type=patient['patient_type'],
            vitals=vitals,
            ml_prediction=prediction,
            nurse_in_ble_range=nurse_in_ble_range,
            nurse_sessions=nurses_in_proximity
        )
        
        # Step 8: Log alarm event
        # Build clean vitals dict (strip internal metadata key before DB/broadcast)
        broadcast_vitals = {k: v for k, v in vitals.items() if not k.startswith("_")}

        # Step 8: Log alarm event
        alarm_event = await database.log_alarm_event(
            patient_id=patient['id'],
            vitals=broadcast_vitals,
            alarm_status=alarm_decision.action,
            proximity_alert_sent=alarm_decision.route_to_nurse,
            nurse_in_proximity=nurse_in_ble_range
        )
        
        # Step 9: Route alerts
        result = {
            "patient_id": patient['id'],
            "patient_name": patient['name'],
            "patient_type": patient['patient_type'],
            "vitals": broadcast_vitals,
            "estimated_fields": vitals.get("_estimated_fields", []),
            "hardware_mode": is_hardware_mode,
            "ml_prediction": prediction,
            "risk_level": ml_result.get("risk_level", "Unknown"),
            "risk_score": ml_result.get("risk_score", 0),
            "alarm_decision": alarm_decision.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to nurse proximity alerts
        if alarm_decision.route_to_nurse:
            for nurse_session in alarm_decision.nurse_sessions:
                await manager.send_to_nurse(nurse_session, {
                    "type": "VIBRATION_ALERT",
                    "patient": patient['name'],
                    "vitals": broadcast_vitals,
                    "estimated_fields": vitals.get("_estimated_fields", []),
                    "message": alarm_decision.message
                })
        
        # Broadcast to dashboard
        if alarm_decision.route_to_dashboard or alarm_decision.action == "SUPPRESS":
            await manager.broadcast(result)
            print(f"📡 Sensor data broadcast to {len(manager.active_connections)} dashboard connection(s)")
        
        print(f"📊 Sensor data processed - Patient: {patient['name']}, Action: {alarm_decision.action}")
        
        return {
            "status": "success",
            "alarm_event_id": alarm_event['id'],
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process sensor data: {str(e)}")


# ========== WebSocket Endpoints ==========

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main dashboard WebSocket connection"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Connected to dashboard WebSocket")
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)
        print(f"[WS] Dashboard client disconnected. Active connections: {len(manager.active_connections)}")


@app.websocket("/ws/nurse/{session_id}")
async def nurse_websocket_endpoint(session_id: str, websocket: WebSocket):
    """Nurse proximity alert WebSocket connection"""
    await manager.connect_nurse(session_id, websocket)
    print(f"🟢 Nurse WebSocket connected: {session_id}")
    try:
        # Send initial connection confirmation
        try:
            await websocket.send_text(json.dumps({
                "event": "connected",
                "session_id": session_id,
                "message": "Nurse WebSocket connected successfully"
            }))
            print(f"✅ Sent connection confirmation to {session_id}")
        except Exception as e:
            print(f"⚠️ Failed to send initial message to {session_id}: {e}")
        
        # Keep connection alive by waiting for disconnect or messages
        while True:
            try:
                # Wait for messages with timeout to check connection health
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                print(f"📩 Received from nurse {session_id}: {data}")
                # Echo back or handle nurse app messages if needed
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                try:
                    await websocket.send_text(json.dumps({"event": "heartbeat", "timestamp": datetime.now().isoformat()}))
                    print(f"💓 Sent heartbeat to {session_id}")
                except:
                    print(f"⚠️ Failed to send heartbeat to {session_id}, connection may be dead")
                    break
                continue
    except WebSocketDisconnect:
        print(f"🔴 Nurse WebSocket disconnected: {session_id}")
        manager.disconnect_nurse(session_id)
    except Exception as e:
        print(f"❌ Nurse WebSocket error for {session_id}: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect_nurse(session_id)


# ========== WebRTC Signaling ==========
# Simple lobby: one broadcaster + N viewers in a named room.
# Backend only relays JSON signaling messages — no media passes through.

_webrtc_rooms: dict[str, dict] = {}  # room_id -> {"broadcaster": ws | None, "viewers": [ws]}


@app.websocket("/ws/webrtc/{room_id}/{role}")
async def webrtc_signaling(room_id: str, role: str, websocket: WebSocket):
    """
    WebRTC signaling relay.
    role = "broadcaster"  →  sends offer + ICE candidates to all viewers
    role = "viewer"       →  receives offer, sends answer back to broadcaster
    """
    await websocket.accept()
    print(f"[WebRTC] {role} joined room '{room_id}'")

    # Ensure room exists
    if room_id not in _webrtc_rooms:
        _webrtc_rooms[room_id] = {"broadcaster": None, "viewers": []}

    room = _webrtc_rooms[room_id]

    if role == "broadcaster":
        room["broadcaster"] = websocket
    else:
        room["viewers"].append(websocket)
        # Tell the broadcaster that a new viewer joined so it can send a fresh offer
        if room["broadcaster"]:
            try:
                await room["broadcaster"].send_text(json.dumps({"type": "viewer_joined"}))
            except Exception:
                pass

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if role == "broadcaster":
                # Forward offer / ICE to ALL viewers
                dead = []
                for v in room["viewers"]:
                    try:
                        await v.send_text(raw)
                    except Exception:
                        dead.append(v)
                for d in dead:
                    room["viewers"].remove(d)
            else:
                # Forward answer / ICE back to broadcaster
                if room["broadcaster"]:
                    try:
                        await room["broadcaster"].send_text(raw)
                    except Exception:
                        room["broadcaster"] = None

    except (WebSocketDisconnect, Exception) as exc:
        print(f"[WebRTC] {role} left room '{room_id}': {exc}")
        if role == "broadcaster":
            room["broadcaster"] = None
            # Notify viewers that the stream ended
            for v in room["viewers"]:
                try:
                    await v.send_text(json.dumps({"type": "broadcaster_left"}))
                except Exception:
                    pass
        else:
            if websocket in room["viewers"]:
                room["viewers"].remove(websocket)
        # Clean up empty rooms
        if room["broadcaster"] is None and not room["viewers"]:
            _webrtc_rooms.pop(room_id, None)


# ========== LEGACY ENDPOINTS (for backward compatibility) ==========

@app.post("/predict_critical")
def predict_critical(data: CriticalPatientData):
    if not critical_model:
        raise HTTPException(status_code=500, detail="Critical model not loaded")
    
    df = pd.DataFrame([data.dict()])
    try:
        prediction = critical_model.predict(df)[0]
        return {"alarm_status": int(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_general")  
def predict_general(data: GeneralPatientData):
    if not general_model:
        raise HTTPException(status_code=500, detail="General model not loaded")
        
    df = pd.DataFrame([data.dict()])
    try:
        prediction = general_model.predict(df)[0]
        return {"alarm_status": int(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {
        "message": "Hospital Alarm Fatigue Monitoring API - Patient-Centric System with Mock Data",
        "status": "running",
        "models": {
            "critical": "loaded" if ml_predictor._critical_bundle else "not loaded",
            "general": "loaded" if ml_predictor._general_bundle else "not loaded"
        },
        "endpoints": {
            "patient_management": [
                "/api/patient/admit", 
                "/api/patient/discharge/{id}", 
                "/api/patient/active",
                "/api/patient/{id}",
                "/api/patients/discharged",
                "/api/patients/statistics"
            ],
            "vital_signs": [
                "/api/patient/{id}/vitals",
                "/api/patient/{id}/vitals/latest",
                "/api/patient/{id}/vitals/simulate"
            ],
            "alarm_history": [
                "/api/patient/{id}/alarm-history"
            ],
            "nurse_proximity": [
                "/api/nurse/register", 
                "/api/nurse/proximity", 
                "/api/nurse/status/{session_id}"
            ],
            "sensor_data": ["/api/sensor-data"],
            "websockets": ["/ws", "/ws/nurse/{session_id}"],
            "camera": ["/stream"]
        },
        "features": {
            "mock_data": "Auto-generates realistic medical profiles, vital signs, and ML predictions",
            "vital_simulation": "Background task generates vital signs every 8 seconds for active patients",
            "medical_history": "Complete patient profiles with conditions, allergies, medications",
            "discharged_history": "Unlimited patient records - all data permanently stored",
            "alarm_policy": "ML-based with BLE proximity routing",
            "camera_stream": "Live laptop webcam feed for patient monitoring"
        }
    }


@app.get("/snapshot")
async def snapshot():
    """
    Returns the latest JPEG frame from the laptop webcam.
    camera_mgr captures frames continuously in a background thread,
    so this endpoint returns instantly from a cached buffer.
    """
    frame_bytes = camera_mgr.get_jpeg()
    if frame_bytes is None:
        raise HTTPException(status_code=503, detail="Camera warming up, try again in 3 seconds")

    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        }
    )


@app.get("/camera")
async def camera_page():
    """
    HTML page with JS polling of /snapshot every 300 ms.
    Load this URL in Android WebView instead of /stream.
    (WebView cannot render multipart/x-mixed-replace MJPEG streams.)
    """
    html = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#000; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; }
  img#feed { width:100%; max-width:640px; display:block; }
  #status { color:#fff; font-family:sans-serif; font-size:13px; padding:6px; opacity:0.7; }
</style>
</head>
<body>
  <img id="feed" alt="Live Feed" />
  <div id="status">Opening camera...</div>
<script>
  var img = document.getElementById('feed');
  var status = document.getElementById('status');
  var base = window.location.origin;
  var errors = 0;
  var started = Date.now();
  function loadFrame() {
    var t = new Date().getTime();
    var src = base + '/snapshot?t=' + t;
    var tempImg = new Image();
    tempImg.onload = function() {
      img.src = tempImg.src;
      status.textContent = 'Live \u25cf';
      errors = 0;
      setTimeout(loadFrame, 300);
    };
    tempImg.onerror = function() {
      errors++;
      var elapsed = Math.round((Date.now() - started) / 1000);
      if (elapsed < 5) {
        status.textContent = 'Opening camera... (' + elapsed + 's)';
        setTimeout(loadFrame, 800);
      } else {
        status.textContent = 'Reconnecting... (' + errors + ')';
        setTimeout(loadFrame, 1500);
      }
    };
    tempImg.src = src;
  }
  loadFrame();
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/stream")
async def video_stream():
    """
    MJPEG video stream from laptop webcam.
    Mobile app displays this when viewing alerted patients.
    Uses the persistent camera_mgr so the camera is already warm.
    """
    def generate():
        try:
            while True:
                frame_bytes = camera_mgr.get_jpeg()
                if frame_bytes is None:
                    break
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"❌ Camera stream error: {e}")

    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


# ========== HARDWARE MODE APIs ==========

@app.post("/api/hardware/tamper/{patient_id}")
async def tamper_hardware_vitals(patient_id: int, scenario: str = "NORMAL"):
    """
    Manual tampering for hardware mode - triggers specific vital scenarios
    Scenarios: NORMAL, HIGH_HR, LOW_SPO2, HIGH_TEMP, CRITICAL
    """
    patient = await database.get_patient_by_id(patient_id)
    if not patient or patient['status'] != 'ACTIVE':
        raise HTTPException(status_code=404, detail="Active patient not found")
    
    # Generate base vitals
    vitals = {
        "HR": 75,
        "SpO2": 98,
        "Temp": 37.0,
        "BP_sys": 120,
        "BP_dia": 80,
        "RR": 16,
        "Glucose": 100
    }
    
    # Apply scenario tampering
    if scenario == "HIGH_HR":
        vitals["HR"] = 125
    elif scenario == "LOW_SPO2":
        vitals["SpO2"] = 85
    elif scenario == "HIGH_TEMP":
        vitals["Temp"] = 39.5
    elif scenario == "CRITICAL":
        vitals["HR"] = 145
        vitals["SpO2"] = 82
        vitals["Temp"] = 40.2
        vitals["BP_sys"] = 190
    
    # Log to database
    await database.log_vital_signs(
        patient_id=patient_id,
        heart_rate=int(vitals['HR']),
        spo2=int(vitals['SpO2']),
        temperature=float(vitals['Temp']),
        bp_systolic=int(vitals['BP_sys']),
        bp_diastolic=int(vitals['BP_dia']),
        respiratory_rate=int(vitals['RR']),
        blood_glucose=int(vitals['Glucose'])
    )
    
    # Broadcast to dashboard
    ml_prediction = mock_data.mock_ml_prediction(vitals, patient['patient_type'])
    vital_update_msg = {
        "event": "vital_signs_update",
        "patient_id": patient_id,
        "patient_name": patient['name'],
        "patient_type": patient['patient_type'],
        "vitals": vitals,
        "ml_prediction": ml_prediction,
        "timestamp": datetime.now().isoformat(),
        "tampered": True,
        "scenario": scenario
    }
    await manager.broadcast(vital_update_msg)
    
    return {
        "success": True,
        "scenario": scenario,
        "vitals": vitals,
        "ml_prediction": ml_prediction
    }


@app.get("/api/config")
async def get_config():
    """
    Get backend configuration information.
    Returns network URLs for mobile app and frontend configuration.
    """
    return config.Config.get_connection_info()


@app.get("/qr")
async def qr_page():
    """Serve an HTML page with a scannable QR code that opens the frontend dashboard."""
    # QR encodes the FRONTEND url (port 3000) so scanning opens the web dashboard
    backend_url = config.Config.get_network_url()          # e.g. http://10.x.x.x:8000
    frontend_url = backend_url.rsplit(":", 1)[0] + ":3000" # swap to port 3000
    try:
        import qrcode
        import io, base64
        qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
        qr.add_data(frontend_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:280px;height:280px;" />'
    except Exception:
        img_tag = "<p style='color:red'>Install qrcode[pil] to show QR image</p>"
    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Open Dashboard</title>
    <style>body{{font-family:sans-serif;text-align:center;padding:30px;background:#f0f4f8}}
    .card{{background:white;border-radius:16px;padding:30px;display:inline-block;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
    h2{{color:#1976d2;margin-bottom:4px}}p{{color:#555;margin:6px 0}}
    .url{{background:#e3f2fd;padding:10px 18px;border-radius:8px;font-family:monospace;font-size:15px;color:#0d47a1;margin:14px 0}}
    </style></head><body>
    <div class='card'>
    <h2>Patient Monitoring Dashboard</h2>
    <p>Scan to open the dashboard on your phone browser</p>
    {img_tag}
    <div class='url'>{frontend_url}</div>
    <p style='font-size:13px;color:#888'>Or type the URL above into your browser</p>
    </div></body></html>"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    
    # Print startup banner with QR code
    config.Config.print_startup_banner(include_qr=True)
    
    # Start server using configuration
    uvicorn.run(
        app, 
        host=config.Config.HOST, 
        port=config.Config.PORT
    )
