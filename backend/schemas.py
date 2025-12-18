from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# ========== LEGACY SCHEMAS (for ML models) ==========

class GeneralPatientData(BaseModel):
    BP_sys: float
    BP_dia: float
    HR: float
    O2: float
    Temp: float
    Glucose: float
    nurse_nearby: int

class CriticalPatientData(BaseModel):
    BP_sys: float
    BP_dia: float
    HR: float
    O2: float
    Temp: float
    ECG: float
    NeurologicalScore: float
    nurse_nearby: int

class PredictRequest(BaseModel):
    ward: str  # "critical" or "general"
    data: Dict[str, Any]

class PatientProfile(BaseModel):
    type: str
    conditions: List[str]
    medications: List[str]
    age: int
    vitals_modifiers: Dict[str, Any]


# ========== NEW PATIENT MANAGEMENT SCHEMAS ==========

class PatientAdmit(BaseModel):
    """Request to admit a new patient"""
    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., gt=0, lt=150)
    problem: str = Field(..., min_length=1)
    patient_type: str = Field(..., pattern="^(GENERAL|CRITICAL)$")
    demo_mode: bool = False
    demo_scenario: Optional[str] = Field(None, pattern="^(NORMAL|MILD_DETERIORATION|CRITICAL_EMERGENCY|FALSE_POSITIVE)?$")
    # Optional medical information
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    medical_history: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[Dict[str, str]]] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    # Disease profile information
    disease: Optional[str] = None
    body_strength: Optional[str] = Field(None, pattern="^(strong|average|weak)?$")
    genetic_condition: Optional[str] = Field(None, pattern="^(healthy|hypertension_prone|diabetes_prone)?$")
    weight: Optional[float] = None
    height: Optional[float] = None
    medical_history: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[Dict[str, Any]]] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(BaseModel):
    """Patient data response"""
    id: int
    name: str
    age: int
    problem: str
    patient_type: str
    status: str
    demo_mode: bool
    demo_scenario: Optional[str]
    admission_time: datetime
    discharge_time: Optional[datetime]
    band_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    # Extended medical information
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    medical_history: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[Dict[str, Any]]] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    # Disease profile information
    disease: Optional[str] = None
    body_strength: Optional[str] = None
    genetic_condition: Optional[str] = None


class BandAssignment(BaseModel):
    """Band assignment info"""
    band_id: str
    patient_id: int
    assigned_at: datetime
    released_at: Optional[datetime] = None


class AlarmEventResponse(BaseModel):
    """Alarm event data"""
    id: int
    patient_id: int
    vitals: Dict[str, Any]
    alarm_status: str
    proximity_alert_sent: bool
    nurse_in_proximity: bool
    timestamp: datetime


# ========== SENSOR DATA SCHEMAS ==========

class RealSensorData(BaseModel):
    """Data from ESP32 sensors with band_id and BLE proximity"""
    band_id: str = Field(default="BAND_01")
    HR: float  # From MAX30100
    SpO2: float  # From MAX30100
    Temp: float  # From LM35/MLX90614
    ble_devices_nearby: List[str] = Field(default_factory=list)  # List of detected nurse session IDs
    timestamp: Optional[Union[str, int, float]] = None
    demo_mode: bool = False  # Enable vital tampering for demo


# ========== VITAL SIGNS SCHEMAS ==========

class VitalSignsLog(BaseModel):
    """Vital signs reading"""
    id: int
    patient_id: int
    heart_rate: float
    spo2: float
    temperature: float
    bp_systolic: float
    bp_diastolic: float
    respiratory_rate: Optional[float]
    blood_glucose: Optional[float]
    timestamp: datetime


class MockMLPrediction(BaseModel):
    """Mock ML prediction response"""
    prediction: int  # 0 = safe, 1 = alarm
    confidence: float
    risk_score: int
    risk_factors: List[str]
    recommendation: str
    model_version: str
    timestamp: str


# ========== NURSE PROXIMITY SCHEMAS ==========

class NurseRegister(BaseModel):
    """Register nurse device for proximity monitoring"""
    device_info: Optional[str] = None


class NurseProximityUpdate(BaseModel):
    """Update nurse proximity with detected BLE devices"""
    session_id: str
    ble_devices_nearby: List[str]  # List of detected band IDs
    rssi_values: Optional[Dict[str, int]] = None  # Optional RSSI signal strength
    
    # Alias for backward compatibility
    @property
    def ble_devices(self):
        return self.ble_devices_nearby


class NurseSessionResponse(BaseModel):
    """Nurse session data"""
    session_id: str
    device_info: Optional[str]
    registered_at: datetime
    last_proximity_update: Optional[datetime]
    ble_devices_nearby: List[str]
    in_proximity: bool = False


# ========== ALARM DECISION SCHEMAS ==========

class AlarmDecision(BaseModel):
    """Alarm routing decision from alarm policy"""
    action: str  # SUPPRESS, PROXIMITY_ALERT, DASHBOARD_ALERT
    alarm_active: bool
    message: str
    route_to_nurse: bool = False
    route_to_dashboard: bool = False
    nurse_sessions: List[str] = Field(default_factory=list)  # Session IDs to notify