"""
Alarm Policy Module
Implements patient-type-based alarm routing with BLE proximity detection
"""
import random
from typing import Dict, Any, List
from schemas import AlarmDecision


# ========== DEMO MODE VITAL TAMPERING ==========

def apply_demo_tampering(vitals: Dict[str, Any], scenario: str, patient_type: str) -> Dict[str, Any]:
    """
    Apply controlled vital tampering for demonstration purposes
    
    Scenarios:
    - NORMAL: No tampering, vitals remain as-is
    - MILD_DETERIORATION: Slightly abnormal vitals
    - CRITICAL_EMERGENCY: Severely abnormal vitals
    - FALSE_POSITIVE: Normal vitals but edge cases
    """
    tampered = vitals.copy()
    
    if scenario == "NORMAL":
        return tampered
    
    elif scenario == "MILD_DETERIORATION":
        if patient_type == "GENERAL":
            # Mild hypertension, slight fever
            tampered["BP_sys"] = random.uniform(140, 155)
            tampered["BP_dia"] = random.uniform(90, 95)
            tampered["Temp"] = random.uniform(37.5, 38.2)
            tampered["HR"] = random.uniform(90, 105)
        else:  # CRITICAL
            # Moderate tachycardia, low SpO2
            tampered["HR"] = random.uniform(110, 130)
            tampered["SpO2"] = random.uniform(88, 92)
            tampered["BP_sys"] = random.uniform(160, 175)
    
    elif scenario == "CRITICAL_EMERGENCY":
        if patient_type == "GENERAL":
            # Severe hypertension, high fever
            tampered["BP_sys"] = random.uniform(180, 200)
            tampered["BP_dia"] = random.uniform(110, 120)
            tampered["Temp"] = random.uniform(39.5, 40.5)
            tampered["HR"] = random.uniform(120, 140)
        else:  # CRITICAL
            # Life-threatening vitals
            tampered["HR"] = random.uniform(150, 180)
            tampered["SpO2"] = random.uniform(75, 85)
            tampered["BP_sys"] = random.uniform(200, 220)
            tampered["Temp"] = random.uniform(40, 41)
    
    elif scenario == "FALSE_POSITIVE":
        # Vitals at edge of normal range
        tampered["HR"] = random.choice([59, 101])  # Just outside normal 60-100
        tampered["BP_sys"] = random.choice([139, 141])  # Around 140 threshold
        tampered["SpO2"] = random.choice([94, 95])  # Lower normal
        tampered["Temp"] = random.choice([37.4, 37.6])  # Slightly elevated
    
    return tampered


# ========== ALARM SUPPRESSION LOGIC ==========

def should_suppress_general_alarm(vitals: Dict[str, Any], ml_prediction: int) -> bool:
    """
    Aggressive alarm suppression for GENERAL ward patients
    
    Suppression rules:
    1. If ML predicts safe (0), always suppress
    2. If vitals are only mildly abnormal, suppress
    3. If multiple vitals are critical, don't suppress
    """
    if ml_prediction == 0:
        return True
    
    # Check severity
    critical_count = 0
    
    hr = vitals.get("HR", 75)
    if hr > 130 or hr < 50:
        critical_count += 1
    
    spo2 = vitals.get("SpO2", 98)
    if spo2 < 88:
        critical_count += 1
    
    temp = vitals.get("Temp", 36.5)
    if temp > 39.5 or temp < 35:
        critical_count += 1
    
    bp_sys = vitals.get("BP_sys", 120)
    if bp_sys > 180 or bp_sys < 90:
        critical_count += 1
    
    # Suppress if less than 2 critical vitals
    return critical_count < 2


def should_suppress_critical_alarm(ml_prediction: int) -> bool:
    """
    Minimal suppression for CRITICAL ward patients
    Only suppress if ML is very confident it's safe
    """
    return ml_prediction == 0


# ========== MAIN ALARM EVALUATION ==========

def evaluate_alarm(
    patient_type: str,
    vitals: Dict[str, Any],
    ml_prediction: int,
    nurse_in_ble_range: bool,
    nurse_sessions: List[str] = None
) -> AlarmDecision:
    """
    Main alarm policy evaluation with patient-type-based routing
    
    Routing Logic:
    - GENERAL + nurse in BLE range + alarm → PROXIMITY_ALERT (vibrate nurse phone)
    - GENERAL + no nurse nearby + alarm → DASHBOARD_ALERT
    - GENERAL + suppressed → SUPPRESS
    - CRITICAL + alarm → DASHBOARD_ALERT (always, ignore proximity)
    - CRITICAL + suppressed → SUPPRESS
    
    Returns:
        AlarmDecision with routing information
    """
    if nurse_sessions is None:
        nurse_sessions = []
    
    # GENERAL WARD LOGIC
    if patient_type == "GENERAL":
        # Check if alarm should be suppressed
        if should_suppress_general_alarm(vitals, ml_prediction):
            return AlarmDecision(
                action="SUPPRESS",
                alarm_active=False,
                message="Alarm suppressed - vitals within acceptable range for general ward",
                route_to_nurse=False,
                route_to_dashboard=False,
                nurse_sessions=[]
            )
        
        # Alarm needed - check nurse proximity
        if nurse_in_ble_range and nurse_sessions:
            return AlarmDecision(
                action="PROXIMITY_ALERT",
                alarm_active=True,
                message="Nurse in proximity - sending vibration alert to mobile device",
                route_to_nurse=True,
                route_to_dashboard=False,
                nurse_sessions=nurse_sessions
            )
        else:
            return AlarmDecision(
                action="DASHBOARD_ALERT",
                alarm_active=True,
                message="No nurse in proximity - escalating to dashboard",
                route_to_nurse=False,
                route_to_dashboard=True,
                nurse_sessions=[]
            )
    
    # CRITICAL WARD LOGIC
    elif patient_type == "CRITICAL":
        # Minimal suppression
        if should_suppress_critical_alarm(ml_prediction):
            return AlarmDecision(
                action="SUPPRESS",
                alarm_active=False,
                message="ML confident vitals are safe for critical patient",
                route_to_nurse=False,
                route_to_dashboard=False,
                nurse_sessions=[]
            )
        
        # Always escalate to dashboard for critical patients (ignore nurse proximity)
        return AlarmDecision(
            action="DASHBOARD_ALERT",
            alarm_active=True,
            message="Critical patient alarm - immediate dashboard escalation",
            route_to_nurse=False,
            route_to_dashboard=True,
            nurse_sessions=[]
        )
    
    else:
        # Unknown patient type - default to dashboard alert
        return AlarmDecision(
            action="DASHBOARD_ALERT",
            alarm_active=True,
            message=f"Unknown patient type '{patient_type}' - defaulting to dashboard alert",
            route_to_nurse=False,
            route_to_dashboard=True,
            nurse_sessions=[]
        )


# ========== UTILITY FUNCTIONS ==========

def format_vitals_for_ml(vitals: Dict[str, Any], patient_type: str) -> Dict[str, Any]:
    """
    Format real sensor vitals into ML model feature format
    """
    base_features = {
        "BP_sys": vitals.get("BP_sys", 120),
        "BP_dia": vitals.get("BP_dia", 80),
        "HR": vitals.get("HR", 75),
        "O2": vitals.get("SpO2", 98),  # Map SpO2 to O2
        "Temp": vitals.get("Temp", 36.5),
        "nurse_nearby": 1 if vitals.get("nurse_nearby", False) else 0
    }
    
    if patient_type == "GENERAL":
        base_features["Glucose"] = vitals.get("Glucose", 100)
    elif patient_type == "CRITICAL":
        base_features["ECG"] = vitals.get("ECG", 0)
        base_features["NeurologicalScore"] = vitals.get("NeurologicalScore", 15)
    
    return base_features
