"""
vital_estimator.py  (backend module)
=====================================
Loads the trained regression models and estimates the 4 vitals that
the hardware cannot physically measure, from the 3 real sensor inputs.

ONLY called in hardware mode.  Simulation mode never touches this file.

Real inputs  (from ESP32 hardware):
    HR      — MAX30102 pulse oximeter
    SpO2    — MAX30102 pulse oximeter
    Temp    — DS18B20 digital temperature sensor

Estimated outputs (labeled "(est.)" everywhere in the system):
    BP_sys  — Systolic Blood Pressure  (mmHg)
    BP_dia  — Diastolic Blood Pressure (mmHg)
    RR      — Respiratory Rate          (breaths/min)
    Glucose — Blood Glucose             (mg/dL)
"""

import os
import joblib
import numpy as np

_PKL_PATH = os.path.join(os.path.dirname(__file__), "vital_estimator.pkl")

_bundle = None   # lazy-loaded

def _load():
    global _bundle
    if _bundle is None:
        try:
            _bundle = joblib.load(_PKL_PATH)
            print("[OK] vital_estimator.pkl loaded (hardware-mode vital estimation enabled)")
        except Exception as e:
            print(f"[WARN] vital_estimator.pkl not found: {e}")
            _bundle = {}
    return _bundle

# All diseases the estimator was trained on (same order as training)
ALL_DISEASES = [
    "Hypertension", "Diabetes Type 2", "Asthma",
    "Mild Pneumonia", "UTI", "Gastroenteritis",
    "Heart Attack", "Stroke", "Severe Pneumonia",
    "Sepsis", "Acute Respiratory Failure",
]


def _news2_partial(hr: float, spo2: float, temp: float) -> int:
    """Partial NEWS2 score from only the 3 available real-sensor vitals."""
    score = 0
    if spo2 <= 91:    score += 3
    elif spo2 <= 93:  score += 2
    elif spo2 <= 95:  score += 1
    if hr <= 40:      score += 3
    elif hr <= 50:    score += 1
    elif hr <= 90:    score += 0
    elif hr <= 110:   score += 1
    elif hr <= 130:   score += 2
    else:             score += 3
    if temp <= 35.0:  score += 3
    elif temp <= 36.0: score += 1
    elif temp <= 38.0: score += 0
    elif temp <= 39.0: score += 1
    else:             score += 2
    return score


def estimate_missing_vitals(
    HR: float,
    SpO2: float,
    Temp: float,
    age: int,
    patient_type: str,   # "GENERAL" or "CRITICAL"
    disease: str = "",
) -> dict:
    """
    Returns a dict with 4 estimated vitals and their estimated=True flag.

    Example return value:
        {
          "BP_sys":   128.4,
          "BP_dia":   82.1,
          "RR":       18.2,
          "Glucose":  105.7,
          "estimated": True,   # always True here — caller uses this flag
        }

    If the model is unavailable (pkl missing), falls back to safe clinical
    defaults so the system continues to function.
    """
    bundle = _load()
    if not bundle or "models" not in bundle:
        # Safe clinical defaults as last-resort fallback
        return {
            "BP_sys":   120.0,
            "BP_dia":   80.0,
            "RR":       16.0,
            "Glucose":  100.0,
            "estimated": True,
        }

    models       = bundle["models"]
    feature_cols = bundle["feature_cols"]
    is_critical  = 1 if patient_type == "CRITICAL" else 0

    # Normalise disease name
    matched_disease = ""
    for d in ALL_DISEASES:
        if d.lower() == (disease or "").lower():
            matched_disease = d
            break

    # Build feature vector (same order as training)
    feature_map = {
        "HR":          HR,
        "SpO2":        SpO2,
        "Temp":        Temp,
        "news2_partial": _news2_partial(HR, SpO2, Temp),
        "age":         age,
        "is_critical": is_critical,
    }
    for d in ALL_DISEASES:
        feature_map[f"disease_{d}"] = int(d == matched_disease)

    x = np.array([[feature_map[f] for f in feature_cols]])

    result = {"estimated": True}
    for target, m in models.items():
        raw = float(m.predict(x)[0])
        # Clip to physiological bounds
        bounds = {
            "BP_sys":  (60,  250),
            "BP_dia":  (30,  150),
            "RR":      (4,   60),
            "Glucose": (40,  600),
        }
        lo, hi = bounds[target]
        result[target] = round(max(lo, min(hi, raw)), 1)

    return result
