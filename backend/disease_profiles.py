"""
Disease-Medication-Vitals Modeling System
Provides realistic disease profiles, medication effects, and vital sign simulation
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random

# ==================== DISEASE DATABASES ====================

GENERAL_WARD_DISEASES = {
    "Pneumonia (Mild)": {
        "symptoms": ["Cough", "Chest pain", "Fatigue", "Shortness of breath"],
        "typical_vitals_impact": {
            "HR": (5, 15),
            "SpO2": (-5, -2),
            "Temp": (1.0, 2.5),
            "RR": (3, 8),
        },
        "medications": [
            {
                "name": "Amoxicillin 500mg",
                "dosage": "500mg",
                "frequency": "Three times daily",
                "vitals_effect": {"Temp": -1.5, "HR": -5}
            },
            {
                "name": "Azithromycin 250mg",
                "dosage": "250mg",
                "frequency": "Once daily",
                "vitals_effect": {"Temp": -1.2, "HR": -3}
            }
        ]
    },
    "UTI (Urinary Tract Infection)": {
        "symptoms": ["Burning urination", "Frequent urination", "Lower abdominal pain", "Fever"],
        "typical_vitals_impact": {
            "HR": (8, 18),
            "Temp": (0.5, 2.0),
            "BP_sys": (5, 15),
        },
        "medications": [
            {
                "name": "Ciprofloxacin 500mg",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "vitals_effect": {"Temp": -1.0, "HR": -5}
            },
            {
                "name": "Nitrofurantoin 100mg",
                "dosage": "100mg",
                "frequency": "Twice daily",
                "vitals_effect": {"Temp": -0.8, "HR": -3}
            }
        ]
    },
    "Gastroenteritis": {
        "symptoms": ["Diarrhea", "Vomiting", "Abdominal cramps", "Dehydration"],
        "typical_vitals_impact": {
            "HR": (10, 25),
            "BP_sys": (-15, -5),
            "BP_dia": (-10, -5),
            "Temp": (0.5, 1.5),
        },
        "medications": [
            {
                "name": "IV Fluids (Normal Saline)",
                "dosage": "1L",
                "frequency": "Every 4 hours",
                "vitals_effect": {"BP_sys": 15, "BP_dia": 10, "HR": -10}
            },
            {
                "name": "Ondansetron 4mg",
                "dosage": "4mg",
                "frequency": "Every 8 hours",
                "vitals_effect": {"HR": -5}
            }
        ]
    },
    "Asthma (Mild Attack)": {
        "symptoms": ["Wheezing", "Shortness of breath", "Chest tightness", "Coughing"],
        "typical_vitals_impact": {
            "SpO2": (-8, -3),
            "RR": (5, 12),
            "HR": (10, 20),
        },
        "medications": [
            {
                "name": "Albuterol Inhaler",
                "dosage": "2 puffs",
                "frequency": "Every 4-6 hours",
                "vitals_effect": {"SpO2": 5, "RR": -8, "HR": 10}
            },
            {
                "name": "Prednisone 40mg",
                "dosage": "40mg",
                "frequency": "Once daily",
                "vitals_effect": {"SpO2": 3, "RR": -5}
            }
        ]
    },
    "Cellulitis": {
        "symptoms": ["Skin redness", "Swelling", "Warmth", "Pain"],
        "typical_vitals_impact": {
            "Temp": (0.8, 2.0),
            "HR": (5, 15),
        },
        "medications": [
            {
                "name": "Cephalexin 500mg",
                "dosage": "500mg",
                "frequency": "Four times daily",
                "vitals_effect": {"Temp": -1.2, "HR": -5}
            },
            {
                "name": "Clindamycin 300mg",
                "dosage": "300mg",
                "frequency": "Three times daily",
                "vitals_effect": {"Temp": -1.0, "HR": -4}
            }
        ]
    },
    "Migraine": {
        "symptoms": ["Severe headache", "Nausea", "Light sensitivity", "Visual disturbances"],
        "typical_vitals_impact": {
            "HR": (5, 15),
            "BP_sys": (10, 20),
            "BP_dia": (5, 15),
        },
        "medications": [
            {
                "name": "Sumatriptan 50mg",
                "dosage": "50mg",
                "frequency": "As needed",
                "vitals_effect": {"BP_sys": -10, "BP_dia": -5, "HR": -8}
            },
            {
                "name": "Ibuprofen 400mg",
                "dosage": "400mg",
                "frequency": "Every 6 hours",
                "vitals_effect": {"BP_sys": -5, "HR": -3}
            }
        ]
    }
}

CRITICAL_WARD_DISEASES = {
    "Myocardial Infarction (Heart Attack)": {
        "symptoms": ["Severe chest pain", "Shortness of breath", "Sweating", "Nausea"],
        "typical_vitals_impact": {
            "HR": (20, 50),
            "BP_sys": (-30, 20),
            "BP_dia": (-20, 10),
            "SpO2": (-10, -3),
            "RR": (5, 15),
        },
        "medications": [
            {
                "name": "Aspirin 325mg",
                "dosage": "325mg",
                "frequency": "Once (loading dose)",
                "vitals_effect": {"HR": -5}
            },
            {
                "name": "Nitroglycerin 0.4mg SL",
                "dosage": "0.4mg",
                "frequency": "Every 5 min PRN",
                "vitals_effect": {"BP_sys": -20, "BP_dia": -15, "HR": 5}
            },
            {
                "name": "Morphine 2-4mg IV",
                "dosage": "2-4mg",
                "frequency": "Every 5-15 min PRN",
                "vitals_effect": {"HR": -15, "RR": -5, "BP_sys": -15}
            },
            {
                "name": "Metoprolol 5mg IV",
                "dosage": "5mg",
                "frequency": "Every 5 min x3",
                "vitals_effect": {"HR": -20, "BP_sys": -15, "BP_dia": -10}
            }
        ]
    },
    "Septic Shock": {
        "symptoms": ["Fever/Hypothermia", "Confusion", "Rapid breathing", "Low BP"],
        "typical_vitals_impact": {
            "HR": (30, 60),
            "BP_sys": (-50, -20),
            "BP_dia": (-30, -15),
            "Temp": (-2.0, 3.0),
            "RR": (10, 25),
            "SpO2": (-15, -5),
        },
        "medications": [
            {
                "name": "Norepinephrine IV",
                "dosage": "0.1-0.5 mcg/kg/min",
                "frequency": "Continuous infusion",
                "vitals_effect": {"BP_sys": 40, "BP_dia": 25, "HR": 10}
            },
            {
                "name": "IV Fluids (Lactated Ringer's)",
                "dosage": "30mL/kg bolus",
                "frequency": "Rapid infusion",
                "vitals_effect": {"BP_sys": 20, "BP_dia": 15, "HR": -15}
            },
            {
                "name": "Broad Spectrum Antibiotics",
                "dosage": "Per protocol",
                "frequency": "Loading dose",
                "vitals_effect": {"Temp": -2.0, "HR": -10}
            }
        ]
    },
    "ARDS (Acute Respiratory Distress Syndrome)": {
        "symptoms": ["Severe dyspnea", "Hypoxemia", "Bilateral lung infiltrates"],
        "typical_vitals_impact": {
            "SpO2": (-25, -10),
            "RR": (15, 35),
            "HR": (20, 40),
            "BP_sys": (-20, 10),
        },
        "medications": [
            {
                "name": "High-flow Oxygen/Mechanical Ventilation",
                "dosage": "FiO2 80-100%",
                "frequency": "Continuous",
                "vitals_effect": {"SpO2": 15, "RR": -10, "HR": -10}
            },
            {
                "name": "Dexamethasone 6mg IV",
                "dosage": "6mg",
                "frequency": "Once daily",
                "vitals_effect": {"SpO2": 5, "RR": -5}
            },
            {
                "name": "Prone Positioning",
                "dosage": "N/A",
                "frequency": "12-16 hours daily",
                "vitals_effect": {"SpO2": 8, "RR": -8}
            }
        ]
    },
    "Stroke (Ischemic)": {
        "symptoms": ["Sudden weakness", "Facial drooping", "Speech difficulty", "Confusion"],
        "typical_vitals_impact": {
            "BP_sys": (20, 50),
            "BP_dia": (10, 30),
            "HR": (-10, 20),
            "RR": (5, 15),
        },
        "medications": [
            {
                "name": "Alteplase (tPA) IV",
                "dosage": "0.9mg/kg",
                "frequency": "One time bolus",
                "vitals_effect": {"BP_sys": -10, "BP_dia": -5}
            },
            {
                "name": "Aspirin 325mg",
                "dosage": "325mg",
                "frequency": "Once (after tPA)",
                "vitals_effect": {"HR": -5}
            },
            {
                "name": "Labetalol IV",
                "dosage": "10-20mg",
                "frequency": "PRN for BP control",
                "vitals_effect": {"BP_sys": -25, "BP_dia": -15, "HR": -10}
            }
        ]
    },
    "DKA (Diabetic Ketoacidosis)": {
        "symptoms": ["Hyperglycemia", "Dehydration", "Fruity breath", "Confusion"],
        "typical_vitals_impact": {
            "Glucose": (150, 400),
            "HR": (20, 40),
            "BP_sys": (-20, -5),
            "RR": (10, 25),
            "Temp": (-1.0, 1.0),
        },
        "medications": [
            {
                "name": "Insulin IV (Regular)",
                "dosage": "0.1 units/kg/hr",
                "frequency": "Continuous infusion",
                "vitals_effect": {"Glucose": -200, "HR": -15}
            },
            {
                "name": "IV Fluids (Normal Saline)",
                "dosage": "1L/hr initially",
                "frequency": "Continuous",
                "vitals_effect": {"BP_sys": 20, "HR": -10}
            },
            {
                "name": "Potassium Chloride",
                "dosage": "20-40 mEq/L",
                "frequency": "In IV fluids",
                "vitals_effect": {"HR": -5}
            }
        ]
    },
    "Pulmonary Embolism": {
        "symptoms": ["Sudden dyspnea", "Chest pain", "Cough", "Hemoptysis"],
        "typical_vitals_impact": {
            "SpO2": (-15, -5),
            "HR": (20, 50),
            "RR": (10, 20),
            "BP_sys": (-25, -5),
        },
        "medications": [
            {
                "name": "Heparin IV",
                "dosage": "80 units/kg bolus",
                "frequency": "Then 18 units/kg/hr",
                "vitals_effect": {"HR": -10}
            },
            {
                "name": "Oxygen Therapy",
                "dosage": "Per saturation",
                "frequency": "Continuous",
                "vitals_effect": {"SpO2": 10, "RR": -5, "HR": -8}
            },
            {
                "name": "Morphine 2-4mg IV",
                "dosage": "2-4mg",
                "frequency": "PRN pain",
                "vitals_effect": {"HR": -10, "RR": -3, "BP_sys": -10}
            }
        ]
    }
}

CONTRAINDICATIONS = {
    ("Aspirin 325mg", "Warfarin"): "Increased bleeding risk",
    ("Aspirin 325mg", "Heparin IV"): "Increased bleeding risk",
    ("Metoprolol 5mg IV", "Albuterol Inhaler"): "Beta-blocker may reduce bronchodilator effectiveness",
    ("Nitroglycerin 0.4mg SL", "Sildenafil"): "Severe hypotension risk",
    ("Morphine 2-4mg IV", "Benzodiazepines"): "Respiratory depression risk",
    ("Insulin IV (Regular)", "Beta-blockers"): "May mask hypoglycemia symptoms",
}

ALLERGY_REACTIONS = {
    "Penicillin": ["Amoxicillin 500mg", "Cephalexin 500mg"],
    "Sulfa drugs": ["Sulfamethoxazole"],
    "NSAIDs": ["Ibuprofen 400mg", "Aspirin 325mg"],
    "Cephalosporins": ["Cephalexin 500mg"],
}

@dataclass
class PatientProfile:
    age: int
    age_category: str
    gender: str
    body_strength: str
    genetic_condition: str
    disease: str
    ward_type: str
    medications: List[Dict]
    allergies: List[str]
    baseline_vitals: Dict[str, float]
    disease_impact: Dict[str, Tuple[float, float]]
    medication_effects: Dict[str, float]

def get_age_category(age: int) -> str:
    if age < 40:
        return "young"
    elif age < 60:
        return "middle_aged"
    elif age < 75:
        return "elderly"
    else:
        return "very_elderly"

def get_baseline_vitals(age_category: str, body_strength: str, genetic_condition: str) -> Dict[str, float]:
    baseline = {
        "HR": 75.0,
        "SpO2": 98.0,
        "Temp": 37.0,
        "BP_sys": 120.0,
        "BP_dia": 80.0,
        "RR": 16.0,
        "Glucose": 95.0,
    }
    
    if age_category == "elderly":
        baseline["HR"] += 10
        baseline["BP_sys"] += 25
        baseline["BP_dia"] += 10
        baseline["SpO2"] -= 2
    elif age_category == "very_elderly":
        baseline["HR"] += 15
        baseline["BP_sys"] += 35
        baseline["BP_dia"] += 15
        baseline["SpO2"] -= 3
    elif age_category == "young":
        baseline["HR"] -= 5
        baseline["BP_sys"] -= 10
        baseline["BP_dia"] -= 5
    
    if body_strength == "weak":
        baseline["HR"] += 8
        baseline["BP_sys"] -= 10
        baseline["SpO2"] -= 1
    elif body_strength == "strong":
        baseline["HR"] -= 5
        baseline["BP_sys"] += 5
    
    if genetic_condition == "hypertension_prone":
        baseline["BP_sys"] += 20
        baseline["BP_dia"] += 10
    elif genetic_condition == "diabetes_prone":
        baseline["Glucose"] += 20
    
    return baseline

def check_medication_safety(medications: List[str], allergies: List[str], existing_meds: List[str] = None) -> Tuple[bool, List[str]]:
    warnings = []
    
    for allergy in allergies:
        if allergy in ALLERGY_REACTIONS:
            contraindicated_meds = ALLERGY_REACTIONS[allergy]
            for med in medications:
                if any(contraindicated in med for contraindicated in contraindicated_meds):
                    warnings.append(f"⚠️ ALLERGY ALERT: Patient allergic to {allergy}, cannot use {med}")
    
    all_meds = medications + (existing_meds or [])
    for i, med1 in enumerate(all_meds):
        for med2 in all_meds[i+1:]:
            key1 = (med1, med2)
            key2 = (med2, med1)
            
            for key in [key1, key2]:
                for contraindication_pair, reason in CONTRAINDICATIONS.items():
                    if (contraindication_pair[0] in key[0] and contraindication_pair[1] in key[1]) or \
                       (contraindication_pair[1] in key[0] and contraindication_pair[0] in key[1]):
                        warnings.append(f"⚠️ CONTRAINDICATION: {key[0]} + {key[1]} - {reason}")
    
    is_safe = len(warnings) == 0
    return is_safe, warnings

def generate_patient_profile(
    age: int,
    gender: str,
    disease: str,
    ward_type: str,
    body_strength: str = "average",
    genetic_condition: str = "healthy",
    allergies: List[str] = None
) -> PatientProfile:
    age_category = get_age_category(age)
    baseline_vitals = get_baseline_vitals(age_category, body_strength, genetic_condition)
    
    disease_db = CRITICAL_WARD_DISEASES if ward_type == "critical" else GENERAL_WARD_DISEASES
    
    if disease not in disease_db:
        raise ValueError(f"Disease '{disease}' not found in {ward_type} ward database")
    
    disease_info = disease_db[disease]
    medications = disease_info["medications"]
    disease_impact = disease_info["typical_vitals_impact"]
    
    med_names = [m["name"] for m in medications]
    is_safe, warnings = check_medication_safety(med_names, allergies or [])
    
    if not is_safe:
        print(f"⚠️ MEDICATION SAFETY WARNINGS for {disease}:")
        for warning in warnings:
            print(f"  {warning}")
    
    medication_effects = {}
    for med in medications:
        for vital, effect in med.get("vitals_effect", {}).items():
            medication_effects[vital] = medication_effects.get(vital, 0) + effect
    
    return PatientProfile(
        age=age,
        age_category=age_category,
        gender=gender,
        body_strength=body_strength,
        genetic_condition=genetic_condition,
        disease=disease,
        ward_type=ward_type,
        medications=medications,
        allergies=allergies or [],
        baseline_vitals=baseline_vitals,
        disease_impact=disease_impact,
        medication_effects=medication_effects
    )

def calculate_current_vitals(profile: PatientProfile, hours_since_admission: float) -> Dict[str, float]:
    current_vitals = profile.baseline_vitals.copy()
    
    for vital, (min_impact, max_impact) in profile.disease_impact.items():
        impact = random.uniform(min_impact, max_impact)
        current_vitals[vital] = current_vitals.get(vital, 0) + impact
    
    medication_effectiveness = min(hours_since_admission / 2.0, 1.0)
    
    for vital, effect in profile.medication_effects.items():
        current_vitals[vital] = current_vitals.get(vital, 0) + (effect * medication_effectiveness)
    
    for vital in current_vitals:
        variation = random.uniform(-2, 2)
        current_vitals[vital] += variation
    
    current_vitals["HR"] = max(30, min(180, current_vitals.get("HR", 75)))
    current_vitals["SpO2"] = max(70, min(100, current_vitals.get("SpO2", 98)))
    current_vitals["Temp"] = max(32, min(42, current_vitals.get("Temp", 37)))
    current_vitals["BP_sys"] = max(50, min(220, current_vitals.get("BP_sys", 120)))
    current_vitals["BP_dia"] = max(30, min(140, current_vitals.get("BP_dia", 80)))
    current_vitals["RR"] = max(8, min(50, current_vitals.get("RR", 16)))
    current_vitals["Glucose"] = max(30, min(600, current_vitals.get("Glucose", 95)))
    
    return current_vitals

def get_alarm_thresholds(profile: PatientProfile) -> Dict[str, Dict[str, float]]:
    if profile.ward_type == "critical":
        thresholds = {
            "HR": {"min": 50, "max": 130},
            "SpO2": {"min": 88, "max": 100},
            "Temp": {"min": 35.5, "max": 38.5},
            "BP_sys": {"min": 85, "max": 180},
            "BP_dia": {"min": 50, "max": 110},
            "RR": {"min": 10, "max": 30},
            "Glucose": {"min": 70, "max": 180},
        }
    else:
        thresholds = {
            "HR": {"min": 55, "max": 115},
            "SpO2": {"min": 92, "max": 100},
            "Temp": {"min": 36.0, "max": 38.3},
            "BP_sys": {"min": 95, "max": 160},
            "BP_dia": {"min": 55, "max": 100},
            "RR": {"min": 12, "max": 25},
            "Glucose": {"min": 80, "max": 140},
        }
    
    if profile.age_category == "elderly":
        thresholds["BP_sys"]["max"] += 20
        thresholds["SpO2"]["min"] -= 2
    elif profile.age_category == "very_elderly":
        thresholds["BP_sys"]["max"] += 30
        thresholds["SpO2"]["min"] -= 3
    
    if "SpO2" in profile.disease_impact:
        min_impact, _ = profile.disease_impact["SpO2"]
        thresholds["SpO2"]["min"] += min_impact / 2
    
    if "HR" in profile.disease_impact:
        _, max_impact = profile.disease_impact["HR"]
        thresholds["HR"]["max"] += max_impact / 2
    
    return thresholds