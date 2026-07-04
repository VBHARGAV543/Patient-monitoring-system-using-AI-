"""
ml_predictor.py
Loads the trained Random Forest .pkl files and provides a single
predict_alarm() function that the backend calls instead of mock_ml_prediction().

The models expect a fixed feature vector built HERE so training and
inference always use identical feature engineering.
"""

import os
import sys

# Make ML/ directory importable for news2.py
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ML")
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

try:
    import joblib
    import numpy as np
    from news2 import score_news2, profile_adjusted_label
    ML_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] ml_predictor: missing dependency ({e}) -- will fall back to NEWS2-only scoring")
    ML_AVAILABLE = False

# ── Model paths ───────────────────────────────────────────────────────────────
_HERE = os.path.dirname(__file__)
_GENERAL_PKL  = os.path.join(_HERE, "..", "ML", "general_model.pkl")
_CRITICAL_PKL = os.path.join(_HERE, "..", "ML", "critical_model.pkl")

_general_bundle  = None
_critical_bundle = None

if ML_AVAILABLE:
    for path, name in [(_GENERAL_PKL, "general"), (_CRITICAL_PKL, "critical")]:
        try:
            bundle = joblib.load(path)
            if name == "general":
                _general_bundle = bundle
            else:
                _critical_bundle = bundle
            print(f"[OK] RF model loaded: {name}")
        except FileNotFoundError:
            print(f"[WARN] {name} model not found at {path} -- run ML/train_{name}.py first")
        except Exception as e:
            print(f"[WARN] Failed to load {name} model: {e}")


# ── Feature builders ──────────────────────────────────────────────────────────

def _build_general_features(vitals: dict, patient_profile=None) -> list:
    """
    Build the feature vector that matches simulate_data_general.py FEATURE_COLS:
    HR, SpO2, Temp, BP_sys, BP_dia, RR, Glucose, news2_score, age,
    has_bp_med, has_glucose_med, has_bronchodilator, has_antibiotic, has_allergy_flag,
    disease_Diabetes Type 2, disease_Gastroenteritis,
    disease_Hypertension, disease_Mild Pneumonia, disease_UTI
    """
    ns = score_news2(
        hr=vitals.get("HR", 75), spo2=vitals.get("SpO2", 98),
        bp_sys=vitals.get("BP_sys", 120), rr=vitals.get("RR", 16),
        temp=vitals.get("Temp", 37.0)
    )

    # Extract patient context from profile (if profile is a disease_profiles.PatientProfile)
    age = 50
    disease = ""
    meds_lower = []
    has_allergy = 0

    if patient_profile is not None:
        age = getattr(patient_profile, "age", 50)
        disease = getattr(patient_profile, "disease", "")
        meds = getattr(patient_profile, "medications", [])
        # medications is a list of dicts with "name" key
        meds_lower = [m.get("name", "").lower() if isinstance(m, dict) else str(m).lower()
                      for m in meds]
        allergies = getattr(patient_profile, "allergies", [])
        has_allergy = int(len(allergies) > 0)

    disease_lower = disease.lower()
    feat = [
        vitals.get("HR", 75),
        vitals.get("SpO2", 98),
        vitals.get("Temp", 37.0),
        vitals.get("BP_sys", 120),
        vitals.get("BP_dia", 80),
        vitals.get("RR", 16),
        vitals.get("Glucose", 100),
        ns,
        age,
        int(any(k in m for m in meds_lower for k in ["amlodipine","losartan","lisinopril","hydrochlorothiazide","metoprolol"])),
        int(any(k in m for m in meds_lower for k in ["metformin","insulin","glipizide","sitagliptin"])),
        int(any(k in m for m in meds_lower for k in ["salbutamol","budesonide","montelukast"])),
        int(any(k in m for m in meds_lower for k in ["amoxicillin","azithromycin","levofloxacin","ciprofloxacin","nitrofurantoin"])),
        has_allergy,
        int("diabet" in disease_lower),
        int("gastro" in disease_lower or "enteritis" in disease_lower),
        int("hypertension" in disease_lower),
        int("pneumonia" in disease_lower),
        int("uti" in disease_lower or "urinary" in disease_lower),
    ]
    return feat


def _build_critical_features(vitals: dict, patient_profile=None) -> list:
    """
    Build the feature vector matching simulate_data_critical.py FEATURE_COLS:
    HR, SpO2, Temp, BP_sys, BP_dia, RR, Glucose, ECG_abnormal, neuro_score,
    news2_score, age, has_vasopressor, has_anticoagulant, has_antibiotic,
    has_bp_med, has_allergy_flag,
    disease_Heart Attack, disease_Sepsis, disease_Severe Pneumonia, disease_Stroke
    """
    neuro_score = vitals.get("neuro_score", 15)
    consciousness = "alert" if neuro_score >= 13 else "confused"
    ns = score_news2(
        hr=vitals.get("HR", 80), spo2=vitals.get("SpO2", 95),
        bp_sys=vitals.get("BP_sys", 110), rr=vitals.get("RR", 18),
        temp=vitals.get("Temp", 37.0), consciousness=consciousness
    )

    age = 60
    disease = ""
    meds_lower = []
    has_allergy = 0

    if patient_profile is not None:
        age = getattr(patient_profile, "age", 60)
        disease = getattr(patient_profile, "disease", "")
        meds = getattr(patient_profile, "medications", [])
        meds_lower = [m.get("name", "").lower() if isinstance(m, dict) else str(m).lower()
                      for m in meds]
        allergies = getattr(patient_profile, "allergies", [])
        has_allergy = int(len(allergies) > 0)

    disease_lower = disease.lower()
    feat = [
        vitals.get("HR", 80),
        vitals.get("SpO2", 95),
        vitals.get("Temp", 37.0),
        vitals.get("BP_sys", 110),
        vitals.get("BP_dia", 70),
        vitals.get("RR", 18),
        vitals.get("Glucose", 100),
        vitals.get("ECG_abnormal", 0),
        neuro_score,
        ns,
        age,
        int(any(k in m for m in meds_lower for k in ["norepinephrine","vasopressin","dopamine"])),
        int(any(k in m for m in meds_lower for k in ["heparin","alteplase","clopidogrel"])),
        int(any(k in m for m in meds_lower for k in ["vancomycin","meropenem","ceftriaxone","piperacillin"])),
        int(any(k in m for m in meds_lower for k in ["labetalol","nitroglycerin","furosemide"])),
        has_allergy,
        int("heart attack" in disease_lower or "myocardial" in disease_lower),
        int("sepsis" in disease_lower),
        int("severe pneumonia" in disease_lower or "respiratory failure" in disease_lower),
        int("stroke" in disease_lower),
    ]
    return feat


# ── Label helpers ─────────────────────────────────────────────────────────────

_LABEL_MAP = {0: "Safe", 1: "Warning", 2: "Critical"}
_PRED_MAP  = {0: 0, 1: 1, 2: 1}     # 2 also counts as alarm (prediction=1)


def _news2_fallback(vitals: dict, patient_type: str, patient_profile=None):
    """
    Pure NEWS2-based fallback when the .pkl doesn't exist yet.
    Still personalised via profile_adjusted_label.
    """
    from news2 import news2_risk_level
    age = 50
    disease = ""
    meds = []
    allergies = []
    if patient_profile is not None:
        age = getattr(patient_profile, "age", 50)
        disease = getattr(patient_profile, "disease", "")
        meds_raw = getattr(patient_profile, "medications", [])
        meds = [m.get("name", "") if isinstance(m, dict) else str(m) for m in meds_raw]
        allergies = getattr(patient_profile, "allergies", [])

    neuro = vitals.get("neuro_score", 15)
    ns = score_news2(
        hr=vitals.get("HR", 75), spo2=vitals.get("SpO2", 98),
        bp_sys=vitals.get("BP_sys", 120), rr=vitals.get("RR", 16),
        temp=vitals.get("Temp", 37.0),
        consciousness="alert" if neuro >= 13 else "confused"
    )
    label = profile_adjusted_label(
        base_score=ns, disease=disease, medications=meds, vitals=vitals, age=age
    )
    _, risk_label = news2_risk_level(ns)
    risk_score = round(ns / 20.0 * 10, 2)   # normalise to 0-10
    return {
        "prediction": int(label >= 1),
        "risk_level": _LABEL_MAP[min(label, 2)],
        "risk_score": risk_score,
        "news2_score": ns,
        "confidence": round(0.55 + min(ns, 10) * 0.03, 2),
        "model_version": "NEWS2-fallback",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def predict_alarm(vitals: dict, patient_type: str, patient_profile=None) -> dict:
    """
    Main entry point called by backend/main.py.

    Returns dict with keys:
        prediction   — 0 (safe) or 1 (alarm)
        risk_level   — "Safe" / "Warning" / "Critical"
        risk_score   — float 0-10 (for frontend gauge)
        news2_score  — raw NEWS2 integer
        confidence   — float 0-1
        model_version— string
    """
    if not ML_AVAILABLE:
        return _news2_fallback(vitals, patient_type, patient_profile)

    is_critical = (patient_type or "").upper() == "CRITICAL"
    bundle = _critical_bundle if is_critical else _general_bundle

    if bundle is None:
        return _news2_fallback(vitals, patient_type, patient_profile)

    model = bundle["model"] if isinstance(bundle, dict) else bundle

    if is_critical:
        feat = _build_critical_features(vitals, patient_profile)
    else:
        feat = _build_general_features(vitals, patient_profile)

    feat_arr = np.array(feat, dtype=float).reshape(1, -1)

    label = int(model.predict(feat_arr)[0])
    proba = model.predict_proba(feat_arr)[0]

    # risk_score: weighted sum of class probabilities (0=safe, 1=warn, 2=crit)
    classes = list(model.classes_)
    risk_score = sum(proba[i] * classes[i] for i in range(len(classes)))
    risk_score = round(float(risk_score) / 2.0 * 10, 2)   # 0-10 scale

    confidence = round(float(max(proba)), 2)
    prediction = int(label >= 1)

    # Always compute NEWS2 for the dashboard display
    ns = score_news2(
        hr=vitals.get("HR", 75), spo2=vitals.get("SpO2", 98),
        bp_sys=vitals.get("BP_sys", 120), rr=vitals.get("RR", 16),
        temp=vitals.get("Temp", 37.0)
    )

    return {
        "prediction": prediction,
        "risk_level": _LABEL_MAP.get(label, "Warning"),
        "risk_score": risk_score,
        "news2_score": ns,
        "confidence": confidence,
        "model_version": "RF_NEWS2_v2.0",
    }
