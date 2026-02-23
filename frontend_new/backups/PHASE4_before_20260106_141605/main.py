from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from schemas import (
    CriticalPatientData, GeneralPatientData, PredictRequest, RealSensorData,
    PatientAdmit, PatientResponse, AlarmEventResponse,
    NurseRegister, NurseProximityUpdate, NurseSessionResponse,
    VitalSignsLog, MockMLPrediction
)
import database
import alarm_policy
import mock_data
import disease_profiles
import os
import json
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import cv2

# Import ML libraries with fallback
try:
    import joblib
    import pandas as pd
    ML_AVAILABLE = True
except Exception as e:
    print(f"⚠️ ML libraries not available: {e}")
    joblib = None
    pd = None
    ML_AVAILABLE = False

# Load ML models
CRITICAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), '../ML/critical_model.pkl')
GENERAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), '../ML/general_model.pkl')

critical_model = None
general_model = None

if ML_AVAILABLE and joblib:
    try:
        critical_model = joblib.load(CRITICAL_MODEL_PATH)
        print("✅ Critical ward model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load critical model: {e}")
        critical_model = None

    try:
        general_model = joblib.load(GENERAL_MODEL_PATH)
        print("✅ General ward model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load general model: {e}")
        general_model = None
else:
    print("⚠️ Skipping ML model loading (libraries not available)")


# Lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.init_db()
    
    # Reload patient profiles for any active patients
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
    
    yield
    
    # Shutdown
    vital_task.cancel()
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
        """Broadcast to main dashboard connections"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

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

# Phase 2: In-memory hardware vitals buffer (30-second TTL)
# Structure: {patient_id: {"vitals": {...}, "timestamp": datetime}}
hardware_vitals_buffer: Dict[int, Dict[str, Any]] = {}
HARDWARE_VITALS_TTL = 30  # seconds

# Background task for simulating vital signs
async def simulate_vitals_background():
    """Background task that continuously generates vital signs for active patients"""
    print("🚀 Starting vital signs background task...")
    while True:
        try:
            # Get active patient
            patient = await database.get_active_patient()
            
            if patient:
                # Phase 2: SIMULATION GATE - Skip hardware mode patients
                if patient.get('hardware_mode', False):
                    print(f"⏭️ Skipping simulation for hardware mode patient: {patient['name']} (ID: {patient['id']})")
                    await asyncio.sleep(8)
                    continue
                
                print(f"✅ Active patient found: {patient['name']} (ID: {patient['id']}, Type: {patient['patient_type']})")
                patient_id = patient['id']
                
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
                
                # Run ML prediction on vitals
                ml_prediction = mock_data.mock_ml_prediction(vitals, patient['patient_type'])
                
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
            "hardware_mode": patient.hardware_mode,  # Phase 1: Real sensor mode
        }
        
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
                    "emergency_contact": patient.emergency_contact or mock_profile.get("emergency_contact"),
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
                "emergency_contact": patient.emergency_contact or mock_profile.get("emergency_contact"),
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


# ========== PHASE 2: HARDWARE VITALS PIPELINE ==========

@app.post("/api/hardware/vitals")
async def receive_hardware_vitals(
    patient_id: int,
    vitals: Dict[str, float],
    timestamp: Optional[str] = None
):
    """
    Phase 2: Receive real hardware sensor vitals (ESP32 + MAX30100)
    Stores in in-memory buffer with 30-second TTL
    Only processes patients with hardware_mode == True
    """
    try:
        # Validate patient exists and is in hardware mode
        patient = await database.get_patient_by_id(patient_id)
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if patient.get('status') != 'ACTIVE':
            raise HTTPException(status_code=400, detail="Patient is not active")
        
        if not patient.get('hardware_mode', False):
            raise HTTPException(
                status_code=400, 
                detail="Patient is not in hardware mode. Enable hardware_mode during admission."
            )
        
        # Store in buffer with timestamp
        hardware_vitals_buffer[patient_id] = {
            "vitals": vitals,
            "timestamp": datetime.now(),
            "received_at": timestamp or datetime.now().isoformat()
        }
        
        print(f"✅ Hardware vitals received for patient {patient_id}: {vitals}")
        
        # Optionally log to database for history
        if 'HR' in vitals and 'SpO2' in vitals and 'Temp' in vitals:
            await database.log_vital_signs(
                patient_id=patient_id,
                heart_rate=int(vitals.get('HR', 0)),
                spo2=int(vitals.get('SpO2', 0)),
                temperature=float(vitals.get('Temp', 0)),
                bp_systolic=int(vitals.get('BP_sys', 0)),
                bp_diastolic=int(vitals.get('BP_dia', 0)),
                respiratory_rate=int(vitals.get('RR', 0)),
                blood_glucose=int(vitals.get('Glucose', 0))
            )
        
        # Broadcast to dashboard and nurses (same pipeline as simulation)
        vital_update_msg = {
            "event": "vital_signs_update",
            "patient_id": patient_id,
            "patient_name": patient['name'],
            "patient_type": patient['patient_type'],
            "vitals": vitals,
            "source": "hardware",
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast(vital_update_msg)
        print(f"📡 Broadcasted hardware vitals to dashboard")
        
        return {
            "status": "success",
            "message": "Hardware vitals received and buffered",
            "patient_id": patient_id,
            "ttl_seconds": HARDWARE_VITALS_TTL
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process hardware vitals: {str(e)}")


@app.get("/api/hardware/vitals/{patient_id}")
async def get_hardware_vitals(patient_id: int):
    """
    Phase 2: Retrieve buffered hardware vitals for a patient
    Returns None if buffer expired (> 30 seconds old)
    """
    try:
        # Check if patient exists and is in hardware mode
        patient = await database.get_patient_by_id(patient_id)
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if not patient.get('hardware_mode', False):
            raise HTTPException(
                status_code=400, 
                detail="Patient is not in hardware mode"
            )
        
        # Check buffer
        if patient_id not in hardware_vitals_buffer:
            return {
                "status": "no_data",
                "message": "No hardware vitals available in buffer",
                "patient_id": patient_id
            }
        
        buffer_entry = hardware_vitals_buffer[patient_id]
        age_seconds = (datetime.now() - buffer_entry["timestamp"]).total_seconds()
        
        # Check TTL
        if age_seconds > HARDWARE_VITALS_TTL:
            # Expired - remove from buffer
            del hardware_vitals_buffer[patient_id]
            return {
                "status": "expired",
                "message": f"Hardware vitals expired (> {HARDWARE_VITALS_TTL}s old)",
                "patient_id": patient_id
            }
        
        # Return fresh data
        return {
            "status": "success",
            "patient_id": patient_id,
            "vitals": buffer_entry["vitals"],
            "received_at": buffer_entry["received_at"],
            "age_seconds": age_seconds,
            "ttl_remaining": HARDWARE_VITALS_TTL - age_seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve hardware vitals: {str(e)}")


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


@app.get("/api/patients/discharged", response_model=List[PatientResponse])
async def get_discharged_patients(limit: Optional[int] = None):
    """
    Get discharged patient history (all records by default, optional limit)
    """
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
        vitals = {
            "HR": sensor_data.HR,
            "SpO2": sensor_data.SpO2,
            "Temp": sensor_data.Temp,
            "BP_sys": 120,  # Default values (would come from additional sensors)
            "BP_dia": 80,
            "Glucose": 100
        }
        
        # Step 3: Apply demo tampering if enabled
        if patient['demo_mode'] and patient['demo_scenario']:
            vitals = alarm_policy.apply_demo_tampering(
                vitals,
                patient['demo_scenario'],
                patient['patient_type']
            )
        
        # Step 4: Format for ML model
        ml_features = alarm_policy.format_vitals_for_ml(vitals, patient['patient_type'])
        df = pd.DataFrame([ml_features])
        
        # Step 5: Run ML prediction
        if patient['patient_type'] == "CRITICAL" and critical_model:
            prediction = int(critical_model.predict(df)[0])
        elif patient['patient_type'] == "GENERAL" and general_model:
            prediction = int(general_model.predict(df)[0])
        else:
            raise HTTPException(status_code=500, detail="ML model not available")
        
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
        alarm_event = await database.log_alarm_event(
            patient_id=patient['id'],
            vitals=vitals,
            alarm_status=alarm_decision.action,
            proximity_alert_sent=alarm_decision.route_to_nurse,
            nurse_in_proximity=nurse_in_ble_range
        )
        
        # Step 9: Route alerts
        result = {
            "patient_id": patient['id'],
            "patient_name": patient['name'],
            "patient_type": patient['patient_type'],
            "vitals": vitals,
            "ml_prediction": prediction,
            "alarm_decision": alarm_decision.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to nurse proximity alerts
        if alarm_decision.route_to_nurse:
            for nurse_session in alarm_decision.nurse_sessions:
                await manager.send_to_nurse(nurse_session, {
                    "type": "VIBRATION_ALERT",
                    "patient": patient['name'],
                    "vitals": vitals,
                    "message": alarm_decision.message
                })
        
        # Broadcast to dashboard
        if alarm_decision.route_to_dashboard or alarm_decision.action == "SUPPRESS":
            await manager.broadcast(result)
        
        print(f"📊 Sensor data processed - Patient: {patient['name']}, Action: {alarm_decision.action}")
        
        return {
            "status": "success",
            "alarm_event_id": alarm_event['id'],
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
            "critical": "loaded" if critical_model else "failed",
            "general": "loaded" if general_model else "failed"
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


@app.get("/stream")
async def video_stream():
    """
    MJPEG video stream from laptop webcam.
    Mobile app displays this when viewing alerted patients.
    """
    def generate():
        camera = cv2.VideoCapture(0)  # Laptop webcam (index 0)
        # Landscape mode with reduced resolution for mobile viewing
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 20)
        
        try:
            while True:
                success, frame = camera.read()
                if not success:
                    print("⚠️ Failed to read frame from camera")
                    break
                
                # Resize to smaller landscape resolution (480x360 for efficient mobile streaming)
                frame = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_AREA)
                
                # Encode frame as JPEG with good quality for clear medical monitoring
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not ret:
                    continue
                    
                frame_bytes = buffer.tobytes()
                
                # MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"❌ Camera stream error: {e}")
        finally:
            camera.release()
            print("📹 Camera released")
    
    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
