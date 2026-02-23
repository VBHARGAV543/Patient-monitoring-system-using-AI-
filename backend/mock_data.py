"""
Mock Data Generator for Patient Monitoring System
Generates realistic medical data, vital signs, and ML predictions
"""
import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# ========== MEDICAL DATA CONSTANTS ==========

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GENDERS = ["Male", "Female"]

COMMON_CONDITIONS = [
    "Hypertension", "Diabetes Type 2", "Asthma", "COPD", "Heart Disease",
    "Arthritis", "Chronic Kidney Disease", "Hyperlipidemia", "Depression",
    "Anxiety Disorder", "Migraine", "Gastroesophageal Reflux Disease"
]

CRITICAL_CONDITIONS = [
    "Acute Myocardial Infarction", "Stroke", "Sepsis", "Pulmonary Embolism",
    "Acute Respiratory Distress Syndrome", "Diabetic Ketoacidosis",
    "Acute Kidney Injury", "Pneumonia", "Congestive Heart Failure"
]

ALLERGIES_LIST = [
    "Penicillin", "Sulfa drugs", "Aspirin", "Ibuprofen", "Latex",
    "Peanuts", "Shellfish", "Eggs", "Codeine", "Morphine", "None"
]

MEDICATIONS = {
    "GENERAL": [
        {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "route": "Oral"},
        {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "route": "Oral"},
        {"name": "Atorvastatin", "dosage": "20mg", "frequency": "Once daily", "route": "Oral"},
        {"name": "Omeprazole", "dosage": "20mg", "frequency": "Once daily", "route": "Oral"},
        {"name": "Acetaminophen", "dosage": "500mg", "frequency": "As needed", "route": "Oral"},
    ],
    "CRITICAL": [
        {"name": "Heparin", "dosage": "5000 units", "frequency": "Every 8 hours", "route": "IV"},
        {"name": "Norepinephrine", "dosage": "0.1 mcg/kg/min", "frequency": "Continuous", "route": "IV"},
        {"name": "Vancomycin", "dosage": "1g", "frequency": "Every 12 hours", "route": "IV"},
        {"name": "Insulin", "dosage": "Sliding scale", "frequency": "As needed", "route": "SC"},
        {"name": "Furosemide", "dosage": "40mg", "frequency": "Twice daily", "route": "IV"},
    ]
}


# ========== PATIENT PROFILE GENERATOR ==========

def generate_patient_profile(patient_type: str = "GENERAL") -> Dict[str, Any]:
    """Generate complete mock patient profile"""
    gender = random.choice(GENDERS)
    age = random.randint(25, 85) if patient_type == "GENERAL" else random.randint(45, 90)
    
    # Medical history
    num_conditions = random.randint(1, 3) if patient_type == "GENERAL" else random.randint(2, 5)
    medical_history = random.sample(COMMON_CONDITIONS, min(num_conditions, len(COMMON_CONDITIONS)))
    
    # Allergies
    num_allergies = random.randint(0, 3)
    allergies = random.sample(ALLERGIES_LIST, min(num_allergies, len(ALLERGIES_LIST)))
    
    # Current medications
    med_list = MEDICATIONS.get(patient_type, MEDICATIONS["GENERAL"])
    num_meds = random.randint(2, 4) if patient_type == "GENERAL" else random.randint(3, 5)
    medications = random.sample(med_list, min(num_meds, len(med_list)))
    
    # Physical attributes
    weight = round(random.uniform(50, 120), 1)
    height = round(random.uniform(150, 190), 1)
    
    return {
        "gender": gender,
        "blood_type": random.choice(BLOOD_TYPES),
        "weight": weight,
        "height": height,
        "medical_history": medical_history,
        "allergies": allergies,
        "current_medications": medications,
        "emergency_contact": f"Contact_{random.randint(1000, 9999)}",
        "emergency_phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    }


# ========== VITAL SIGNS GENERATOR ==========

def generate_mock_vitals(
    patient_type: str = "GENERAL",
    demo_scenario: Optional[str] = None,
    trend: str = "stable"
) -> Dict[str, float]:
    """
    Generate realistic mock vital signs
    
    Args:
        patient_type: "GENERAL" or "CRITICAL"
        demo_scenario: NORMAL, MILD_DETERIORATION, CRITICAL_EMERGENCY, FALSE_POSITIVE
        trend: "stable", "improving", "deteriorating"
    """
    
    # Base normal ranges
    if patient_type == "GENERAL":
        vitals = {
            "HR": round(random.uniform(65, 90), 1),
            "SpO2": round(random.uniform(95, 100), 1),
            "Temp": round(random.uniform(36.5, 37.2), 1),
            "BP_sys": round(random.uniform(110, 130), 1),
            "BP_dia": round(random.uniform(70, 85), 1),
            "RR": round(random.uniform(12, 18), 1),
            "Glucose": round(random.uniform(80, 120), 1),
        }
    else:  # CRITICAL
        vitals = {
            "HR": round(random.uniform(70, 100), 1),
            "SpO2": round(random.uniform(92, 98), 1),
            "Temp": round(random.uniform(36.8, 37.5), 1),
            "BP_sys": round(random.uniform(100, 140), 1),
            "BP_dia": round(random.uniform(65, 90), 1),
            "RR": round(random.uniform(14, 22), 1),
            "Glucose": round(random.uniform(90, 150), 1),
        }
    
    # Apply demo scenario tampering
    if demo_scenario == "MILD_DETERIORATION":
        vitals["HR"] += random.uniform(15, 25)
        vitals["SpO2"] -= random.uniform(2, 5)
        vitals["Temp"] += random.uniform(0.5, 1.0)
        vitals["BP_sys"] += random.uniform(10, 20)
        
    elif demo_scenario == "CRITICAL_EMERGENCY":
        vitals["HR"] += random.uniform(40, 60)
        vitals["SpO2"] -= random.uniform(8, 15)
        vitals["Temp"] += random.uniform(1.5, 2.5)
        vitals["BP_sys"] += random.uniform(30, 50)
        vitals["RR"] += random.uniform(8, 12)
        
    elif demo_scenario == "FALSE_POSITIVE":
        vitals["HR"] = random.choice([59, 101])
        vitals["SpO2"] = random.uniform(93, 95)
        vitals["Temp"] = random.uniform(37.3, 37.6)
        vitals["BP_sys"] = random.choice([139, 141])
    
    # Apply trend
    if trend == "deteriorating":
        vitals["HR"] += random.uniform(5, 15)
        vitals["SpO2"] -= random.uniform(1, 3)
        vitals["Temp"] += random.uniform(0.2, 0.5)
    elif trend == "improving":
        vitals["HR"] -= random.uniform(3, 10)
        vitals["SpO2"] += random.uniform(1, 2)
        vitals["Temp"] -= random.uniform(0.2, 0.4)
    
    # Round all values
    for key in vitals:
        vitals[key] = round(vitals[key], 1)
    
    return vitals


# ========== MOCK ML MODEL ==========

def mock_ml_prediction(
    vitals: Dict[str, float],
    patient_type: str = "GENERAL"
) -> Dict[str, Any]:
    """
    Mock ML model prediction for alarm status
    
    Returns:
        {
            "prediction": 0 or 1 (0 = safe, 1 = alarm),
            "confidence": float (0-1),
            "risk_factors": list of strings,
            "recommendation": string
        }
    """
    
    risk_factors = []
    risk_score = 0
    
    # Evaluate vital signs
    hr = vitals.get("HR", 75)
    if hr > 100:
        risk_factors.append(f"Tachycardia (HR: {hr})")
        risk_score += 2
    elif hr < 60:
        risk_factors.append(f"Bradycardia (HR: {hr})")
        risk_score += 1
    
    spo2 = vitals.get("SpO2", 98)
    if spo2 < 92:
        risk_factors.append(f"Low SpO2 ({spo2}%)")
        risk_score += 3
    elif spo2 < 95:
        risk_factors.append(f"Borderline SpO2 ({spo2}%)")
        risk_score += 1
    
    temp = vitals.get("Temp", 37)
    if temp > 38.0:
        risk_factors.append(f"Fever (Temp: {temp}°C)")
        risk_score += 2
    elif temp < 36.0:
        risk_factors.append(f"Hypothermia (Temp: {temp}°C)")
        risk_score += 2
    
    bp_sys = vitals.get("BP_sys", 120)
    if bp_sys > 160:
        risk_factors.append(f"Severe Hypertension (BP: {bp_sys})")
        risk_score += 2
    elif bp_sys < 90:
        risk_factors.append(f"Hypotension (BP: {bp_sys})")
        risk_score += 2
    
    glucose = vitals.get("Glucose", 100)
    if glucose > 180:
        risk_factors.append(f"Hyperglycemia (Glucose: {glucose})")
        risk_score += 1
    elif glucose < 70:
        risk_factors.append(f"Hypoglycemia (Glucose: {glucose})")
        risk_score += 2
    
    # Determine prediction
    threshold = 2 if patient_type == "GENERAL" else 1  # More sensitive for critical patients
    prediction = 1 if risk_score >= threshold else 0
    
    # Calculate confidence (mock)
    confidence = min(0.95, 0.6 + (risk_score * 0.1))
    
    # Recommendation
    if prediction == 1:
        if risk_score >= 4:
            recommendation = "Immediate intervention required - Multiple critical parameters"
        elif risk_score >= 2:
            recommendation = "Close monitoring recommended - Vitals show concerning trends"
        else:
            recommendation = "Monitor closely - One or more parameters outside normal range"
    else:
        recommendation = "Patient stable - Continue routine monitoring"
    
    return {
        "prediction": prediction,
        "confidence": round(confidence, 2),
        "risk_score": risk_score,
        "risk_factors": risk_factors if risk_factors else ["All vitals within normal range"],
        "recommendation": recommendation,
        "model_version": "MockML_v1.0",
        "timestamp": datetime.now().isoformat()
    }


# ========== VITAL SIGNS SIMULATOR ==========

class VitalSignsSimulator:
    """Simulates realistic vital signs trends over time"""
    
    def __init__(self, patient_id: int, patient_type: str = "GENERAL", demo_scenario: Optional[str] = None):
        self.patient_id = patient_id
        self.patient_type = patient_type
        self.demo_scenario = demo_scenario
        self.trend = "stable"
        self.time_in_trend = 0
        
    def generate_next_reading(self) -> Dict[str, float]:
        """Generate next vital signs reading with temporal consistency"""
        
        # Occasionally change trend
        self.time_in_trend += 1
        if self.time_in_trend > random.randint(5, 15):
            self.trend = random.choice(["stable", "stable", "improving", "deteriorating"])
            self.time_in_trend = 0
        
        return generate_mock_vitals(
            patient_type=self.patient_type,
            demo_scenario=self.demo_scenario,
            trend=self.trend
        )


# ========== UTILITY FUNCTIONS ==========

def calculate_bmi(weight: float, height: float) -> float:
    """Calculate BMI from weight (kg) and height (cm)"""
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def get_bmi_category(bmi: float) -> str:
    """Get BMI category"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def generate_admission_reason(patient_type: str) -> str:
    """Generate realistic admission reason"""
    if patient_type == "GENERAL":
        reasons = [
            "Routine checkup and monitoring",
            "Post-operative care",
            "Chronic condition management",
            "Scheduled procedure",
            "Medication adjustment",
            "Elective surgery recovery",
        ]
    else:  # CRITICAL
        reasons = [
            "Acute chest pain investigation",
            "Respiratory distress",
            "Severe infection requiring IV antibiotics",
            "Post-ICU step-down care",
            "Cardiac monitoring after procedure",
            "Neurological symptoms investigation",
            "Severe metabolic imbalance",
        ]
    
    return random.choice(reasons)
