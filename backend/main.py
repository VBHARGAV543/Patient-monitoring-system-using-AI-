from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from schemas import CriticalPatientData, GeneralPatientData, PredictRequest, RealSensorData
import joblib
import pandas as pd
import os
import json
import random
from typing import Any, Dict, List
from datetime import datetime

app = FastAPI(title="Hospital Alarm Fatigue Monitoring API")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

alarm_toggle_counter = 0
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

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Random patient profile generator
def generate_random_patient_profile():
    """Generate random patient profile for tampering real sensor data"""
    profiles = [
        {
            "type": "healthy_young",
            "conditions": [],
            "medications": [],
            "age": random.randint(18, 35),
            "vitals_modifiers": {
                "HR": lambda x: x + random.randint(-5, 5),
                "O2": lambda x: min(100, x + random.randint(0, 2)),
                "Temp": lambda x: x + random.uniform(-0.2, 0.2),
                "BP_sys": lambda x: random.randint(110, 130),
                "BP_dia": lambda x: random.randint(70, 85),
                "Glucose": lambda x: random.randint(80, 100)
            }
        },
        {
            "type": "diabetic_elderly",
            "conditions": ["diabetes", "mild_hypertension"],
            "medications": ["metformin", "lisinopril"],
            "age": random.randint(60, 80),
            "vitals_modifiers": {
                "HR": lambda x: x + random.randint(10, 25),
                "O2": lambda x: x - random.randint(0, 3),
                "Temp": lambda x: x + random.uniform(-0.3, 0.5),
                "BP_sys": lambda x: random.randint(140, 170),
                "BP_dia": lambda x: random.randint(85, 95),
                "Glucose": lambda x: random.randint(160, 250)
            }
        },
        {
            "type": "cardiac_critical",
            "conditions": ["cardiac_arrhythmia", "heart_failure"],
            "medications": ["beta_blocker", "ace_inhibitor", "diuretic"],
            "age": random.randint(55, 75),
            "vitals_modifiers": {
                "HR": lambda x: x + random.randint(30, 50),
                "O2": lambda x: x - random.randint(8, 15),
                "Temp": lambda x: x + random.uniform(0.0, 1.5),
                "BP_sys": lambda x: random.randint(90, 120),
                "BP_dia": lambda x: random.randint(50, 70),
                "Glucose": lambda x: random.randint(90, 140),
                "ECG": lambda x: 1,  # Abnormal
                "NeurologicalScore": lambda x: random.randint(8, 12)
            }
        },
        {
            "type": "post_surgery",
            "conditions": ["post_operative", "pain_management"],
            "medications": ["morphine", "antibiotics"],
            "age": random.randint(30, 70),
            "vitals_modifiers": {
                "HR": lambda x: x + random.randint(15, 30),
                "O2": lambda x: x - random.randint(2, 8),
                "Temp": lambda x: x + random.uniform(0.5, 2.0),
                "BP_sys": lambda: random.randint(100, 140),
                "BP_dia": lambda x: random.randint(60, 90),
                "Glucose": lambda x: random.randint(100, 160)
            }
        }
    ]
    
    return random.choice(profiles)

def tamper_real_readings(real_vitals: dict, patient_profile: dict) -> dict:
    """Modify real sensor data based on random patient conditions"""
    
    tampered_vitals = real_vitals.copy()
    modifiers = patient_profile["vitals_modifiers"]
    
    # Apply modifications based on patient profile
    for vital, modifier in modifiers.items():
        if vital in ["HR", "O2", "Temp"] and vital in tampered_vitals:
            # Apply modifier to existing real vital (pass the current value)
            tampered_vitals[vital] = modifier(tampered_vitals[vital])
        elif vital == "O2" and "SpO2" in tampered_vitals:
            # Handle SpO2 to O2 mapping
            tampered_vitals[vital] = modifier(tampered_vitals["SpO2"])
        else:
            # Add new vital sign that wasn't measured by sensors (pass dummy value)
            try:
                tampered_vitals[vital] = modifier(0)
            except TypeError:
                # Handle lambda functions that don't expect parameters
                tampered_vitals[vital] = modifier()
    
    # Ensure realistic bounds
    tampered_vitals["HR"] = max(40, min(200, tampered_vitals.get("HR", 75)))
    tampered_vitals["O2"] = max(70, min(100, tampered_vitals.get("O2", 98)))
    tampered_vitals["Temp"] = max(35, min(42, tampered_vitals.get("Temp", 37)))
    
    # Add default values for missing critical care parameters
    if "ECG" not in tampered_vitals:
        tampered_vitals["ECG"] = 0  # Normal by default
    if "NeurologicalScore" not in tampered_vitals:
        tampered_vitals["NeurologicalScore"] = 15  # Normal score
    
    return tampered_vitals

def prepare_ml_features(tampered_vitals: dict, patient_profile: dict, ward: str) -> dict:
    """Convert tampered vitals to ML model expected format with EXACT column order"""
    
    if ward == "general":
        # Exact order from training: BP_sys, BP_dia, HR, Glucose, O2, Temp, nurse_nearby, disease_* (after get_dummies)
        ml_features = {}
        
        # Base features in exact training order
        ml_features["BP_sys"] = tampered_vitals.get("BP_sys", 120)
        ml_features["BP_dia"] = tampered_vitals.get("BP_dia", 80) 
        ml_features["HR"] = tampered_vitals.get("HR", 75)
        ml_features["Glucose"] = tampered_vitals.get("Glucose", 100)
        ml_features["O2"] = tampered_vitals.get("SpO2", tampered_vitals.get("O2", 98))  # Map SpO2 to O2
        ml_features["Temp"] = tampered_vitals.get("Temp", 37)
        ml_features["nurse_nearby"] = tampered_vitals.get("nurse_nearby", 0)
        
        # Disease features (one-hot encoded) - model expects all disease columns
        patient_conditions = [c.lower() for c in patient_profile.get("conditions", [])]
        
        ml_features["disease_Diabetes"] = 1 if "diabetes" in patient_conditions else 0
        ml_features["disease_Hypertension"] = 1 if "hypertension" in patient_conditions else 0
        ml_features["disease_Mild Pneumonia"] = 1 if "mild pneumonia" in patient_conditions or "pneumonia" in patient_conditions else 0
            
    elif ward == "critical":
        # Critical ward feature order (check critical training file for exact order)
        ml_features = {}
        ml_features["BP_sys"] = tampered_vitals.get("BP_sys", 120)
        ml_features["BP_dia"] = tampered_vitals.get("BP_dia", 80)
        ml_features["HR"] = tampered_vitals.get("HR", 75)
        ml_features["O2"] = tampered_vitals.get("SpO2", tampered_vitals.get("O2", 98))
        ml_features["Temp"] = tampered_vitals.get("Temp", 37)
        ml_features["ECG"] = tampered_vitals.get("ECG", 0)
        ml_features["NeurologicalScore"] = tampered_vitals.get("NeurologicalScore", 15)
        ml_features["nurse_nearby"] = tampered_vitals.get("nurse_nearby", 0)
    
    return ml_features

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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

@app.get("/api/alarm-status")
async def get_alarm_status():
    """
    Endpoint for ESP32 #2 to check if alarms should be activated
    """
    global alarm_toggle_counter
    alarm_toggle_counter += 1
    if alarm_toggle_counter % 2 == 0:
        return {
            "general_alarm": True,
            "critical_alarm": False,
            "timestamp": datetime.now().isoformat(),
            "message": "Forced general alarm (test mode)"
        }
    else:
        return {
            "general_alarm": False,
            "critical_alarm": False,
            "timestamp": datetime.now().isoformat(),
            "message": "No alarms currently needed"
        }

@app.post("/api/sensor-data")
async def receive_sensor_data(sensor_data: RealSensorData):
    """
    ESP32 sensor data endpoint - receives real sensor readings
    """
    try:
        # Convert to dict for processing
        real_vitals = {
            "HR": sensor_data.HR,
            "SpO2": sensor_data.SpO2, 
            "Temp": sensor_data.Temp,
            "nurse_nearby": sensor_data.nurse_nearby,
            "ward": sensor_data.ward
        }
        
        # Process through the main prediction pipeline
        result = await predict_new_patient(real_vitals)
        return {"status": "success", "message": "Data received and processed", "result": result}
        
    except Exception as e:
        return {"status": "error", "message": f"Error processing sensor data: {str(e)}"}

@app.post("/predict_new_patient")
async def predict_new_patient(real_vitals: dict):
    """
    Main endpoint for ESP32 integration:
    1. Receives real sensor data
    2. Generates random patient profile  
    3. Tampers readings based on profile
    4. Runs ML prediction
    5. Broadcasts results to frontend
    """
    
    # Step 1: Generate random patient profile
    patient_profile = generate_random_patient_profile()
    
    # Step 2: Tamper real readings based on profile
    tampered_vitals = tamper_real_readings(real_vitals, patient_profile)
    
    # Step 3: Determine ward type and add missing fields
    ward = real_vitals.get("ward", "general")
    tampered_vitals["nurse_nearby"] = real_vitals.get("nurse_nearby", 0)
    
    # Step 4: Prepare data for ML model
    try:
        # Convert tampered vitals to ML model format
        ml_features = prepare_ml_features(tampered_vitals, patient_profile, ward)
        df = pd.DataFrame([ml_features])
        
        # Debug: Print feature info
        print(f"🔍 ML Features for {ward} ward:")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Values: {df.iloc[0].to_dict()}")
        
        if ward == "critical" and critical_model:
            prediction = critical_model.predict(df)[0]
        elif ward == "general" and general_model:
            prediction = general_model.predict(df)[0]
        else:
            raise HTTPException(status_code=500, detail=f"No model available for {ward} ward")
        
        # Step 5: Prepare response
        result = {
            "alarm_status": int(prediction),
            "patient_story": {
                "type": patient_profile["type"],
                "conditions": patient_profile["conditions"],
                "medications": patient_profile["medications"],
                "age": patient_profile["age"]
            },
            "original_vitals": real_vitals,
            "tampered_vitals": tampered_vitals,
            "ward": ward,
            "timestamp": datetime.now().isoformat(),
            "patient_id": f"P{random.randint(1000, 9999)}"
        }
        
        # Step 6: Broadcast to frontend via WebSocket
        await manager.broadcast(result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "Hospital Alarm Fatigue Monitoring API",
        "status": "running",
        "models": {
            "critical": "loaded" if critical_model else "failed",
            "general": "loaded" if general_model else "failed"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)