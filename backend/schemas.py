from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union

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

class RealSensorData(BaseModel):
    """Data from ESP32 sensors"""
    HR: float  # From MAX30100
    SpO2: float  # From MAX30100
    Temp: float  # From LM35 on GPIO34
    nurse_nearby: int  # From Bluetooth detection
    ward: str  # "general" or "critical"
    timestamp: Optional[Union[str, int, float]] = None

class PatientProfile(BaseModel):
    type: str
    conditions: List[str]
    medications: List[str]
    age: int
    vitals_modifiers: Dict[str, Any]