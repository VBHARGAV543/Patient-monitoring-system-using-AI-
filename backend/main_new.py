from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    CriticalPatientData, GeneralPatientData, PredictRequest, RealSensorData,
    PatientAdmit, PatientResponse, AlarmEventResponse,
    NurseRegister, NurseProximityUpdate, NurseSessionResponse
)
import database
import alarm_policy
import joblib
import pandas as pd
import os
import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# Load ML models
CRITICAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), '../ML/critical_model.pkl')
GENERAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), '../ML/general_model.pkl')

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


# Lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.init_db()
    yield
    # Shutdown
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


# ========== PATIENT LIFECYCLE APIs ==========

@app.post("/api/patient/admit", response_model=PatientResponse)
async def admit_patient(patient: PatientAdmit):
    """
    Admit a new patient and bind BAND_01
    """
    try:
        # Check if band is available
        if not await database.is_band_available():
            raise HTTPException(
                status_code=400,
                detail="BAND_01 is currently assigned to another patient. Please discharge the current patient first."
            )
        
        # Create patient record
        patient_record = await database.create_patient(
            name=patient.name,
            age=patient.age,
            problem=patient.problem,
            patient_type=patient.patient_type,
            demo_mode=patient.demo_mode,
            demo_scenario=patient.demo_scenario
        )
        
        # Assign band to patient
        band_assignment = await database.assign_band_to_patient(patient_record['id'])
        
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
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to admit patient: {str(e)}")


@app.post("/api/patient/discharge/{patient_id}")
async def discharge_patient(patient_id: int):
    """
    Discharge a patient and release BAND_01
    """
    try:
        # Get patient info before discharge
        patient = await database.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if patient['status'] == 'DISCHARGED':
            raise HTTPException(status_code=400, detail="Patient already discharged")
        
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
        
        return PatientResponse(**patient)
        
    except Exception as e:
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


# ========== NURSE PROXIMITY APIs ==========

@app.post("/api/nurse/register", response_model=NurseSessionResponse)
async def register_nurse(nurse: NurseRegister):
    """
    Register nurse device for proximity monitoring
    """
    try:
        session_id = str(uuid.uuid4())
        
        session = await database.create_nurse_session(session_id, nurse.device_info)
        
        return NurseSessionResponse(
            **session,
            ble_devices_nearby=[],
            in_proximity=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register nurse: {str(e)}")


@app.post("/api/nurse/proximity")
async def update_nurse_proximity(proximity: NurseProximityUpdate):
    """
    Update nurse proximity with detected BLE devices
    """
    try:
        success = await database.update_nurse_proximity(proximity.session_id, proximity.ble_devices)
        
        if not success:
            raise HTTPException(status_code=404, detail="Nurse session not found")
        
        return {
            "status": "success",
            "session_id": proximity.session_id,
            "devices_detected": len(proximity.ble_devices)
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
    try:
        while True:
            data = await websocket.receive_text()
            # Handle nurse app messages if needed
            await websocket.send_text(f"Connected to nurse WebSocket: {session_id}")
    except WebSocketDisconnect:
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
        "message": "Hospital Alarm Fatigue Monitoring API - Patient-Centric System",
        "status": "running",
        "models": {
            "critical": "loaded" if critical_model else "failed",
            "general": "loaded" if general_model else "failed"
        },
        "endpoints": {
            "patient_management": ["/api/patient/admit", "/api/patient/discharge/{id}", "/api/patient/active"],
            "nurse_proximity": ["/api/nurse/register", "/api/nurse/proximity", "/api/nurse/status/{session_id}"],
            "sensor_data": ["/api/sensor-data"],
            "websockets": ["/ws", "/ws/nurse/{session_id}"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
