"""
NEWS2 Scorer — National Early Warning Score 2
Source: Royal College of Physicians (2017), publicly available clinical standard.
https://www.rcplondon.ac.uk/projects/outputs/national-early-warning-score-news-2

Used as the BASE alarm label generator for training data.
The Random Forest then learns patient-specific adjustments on TOP of this.
"""


def score_news2(hr: float, spo2: float, bp_sys: float, rr: float,
                temp: float, consciousness: str = "alert") -> int:
    """
    Compute official NEWS2 score from vital signs.
    consciousness: 'alert' (normal) or any other string = altered (ACVPU ≠ A)
    Returns integer score 0–20.
    """
    score = 0

    # Respiratory Rate (breaths/min)
    if rr <= 8:
        score += 3
    elif rr <= 11:
        score += 1
    elif rr <= 20:
        score += 0
    elif rr <= 24:
        score += 2
    else:
        score += 3

    # SpO2 % — Scale 1 (standard, non-hypercapnic patients)
    if spo2 <= 91:
        score += 3
    elif spo2 <= 93:
        score += 2
    elif spo2 <= 95:
        score += 1
    else:
        score += 0

    # Systolic Blood Pressure (mmHg)
    if bp_sys <= 90:
        score += 3
    elif bp_sys <= 100:
        score += 2
    elif bp_sys <= 110:
        score += 1
    elif bp_sys <= 219:
        score += 0
    else:
        score += 3

    # Pulse / Heart Rate (bpm)
    if hr <= 40:
        score += 3
    elif hr <= 50:
        score += 1
    elif hr <= 90:
        score += 0
    elif hr <= 110:
        score += 1
    elif hr <= 130:
        score += 2
    else:
        score += 3

    # Consciousness (ACVPU: Alert / Confusion / Voice / Pain / Unresponsive)
    if consciousness != "alert":
        score += 3

    # Temperature (°C)
    if temp <= 35.0:
        score += 3
    elif temp <= 36.0:
        score += 1
    elif temp <= 38.0:
        score += 0
    elif temp <= 39.0:
        score += 1
    else:
        score += 2

    return score


def news2_risk_level(score: int):
    """
    Returns (label_str, label_int) per RCP protocol.
    LOW  → 0, MEDIUM → 1, HIGH → 2
    """
    if score >= 7:
        return "HIGH", 2
    elif score >= 5:
        return "MEDIUM", 1
    else:
        return "LOW", 0


def profile_adjusted_label(base_score: int, disease: str, medications: list,
                            vitals: dict, age: int) -> int:
    """
    Apply personalised adjustments to NEWS2 base score.

    This is the core novelty:
      Same raw vitals → different alarm level depending on:
        - Whether the patient has a medication that SHOULD have corrected the vital
        - Disease-specific expected baselines
        - Age-related risk weighting

    Returns adjusted label int: 0=Safe, 1=Warning, 2=Critical
    """
    adjusted_score = base_score

    hr     = vitals.get("HR", 75)
    spo2   = vitals.get("SpO2", 98)
    bp_sys = vitals.get("BP_sys", 120)
    glucose= vitals.get("Glucose", 100)
    temp   = vitals.get("Temp", 37.0)
    rr     = vitals.get("RR", 16)

    meds_lower = [m.lower() for m in medications]

    bp_med_present = any(k in m for m in meds_lower
                         for k in ["amlodipine", "losartan", "lisinopril",
                                   "hydrochlorothiazide", "metoprolol", "ramipril"])
    glucose_med_present = any(k in m for m in meds_lower
                               for k in ["metformin", "insulin", "glipizide",
                                         "glibenclamide", "sitagliptin"])
    bronchodilator_present = any(k in m for m in meds_lower
                                  for k in ["salbutamol", "albuterol", "budesonide",
                                            "montelukast", "ipratropium", "salmeterol"])
    antibiotic_present = any(k in m for m in meds_lower
                              for k in ["amoxicillin", "azithromycin", "levofloxacin",
                                        "meropenem", "ceftriaxone", "vancomycin",
                                        "ciprofloxacin", "piperacillin"])

    # ── Hypertension: if on BP meds but BP still high → drug failing → escalate ──
    if "hypertension" in disease.lower() and bp_med_present:
        if bp_sys > 155:
            adjusted_score += 2   # Expected to be controlled, but isn't
        elif bp_sys > 145:
            adjusted_score += 1
        # If BP is well controlled (< 130), the raw NEWS2 is correct → no change

    # ── Diabetes: if glucose medication present but glucose still elevated → warn ──
    if "diabet" in disease.lower() and glucose_med_present:
        if glucose > 220:
            adjusted_score += 3   # Medication failing → higher alarm priority
        elif glucose > 180:
            adjusted_score += 1

    # ── Asthma: if bronchodilator present but SpO2 still low → escalate ──
    if "asthma" in disease.lower() and bronchodilator_present:
        if spo2 < 90:
            adjusted_score += 3   # Bronchodilator failed → critical
        elif spo2 < 93:
            adjusted_score += 2

    # ── Pneumonia: if antibiotic present but fever still high → drug not working ──
    if "pneumonia" in disease.lower() or "sepsis" in disease.lower():
        if antibiotic_present and temp > 39.5:
            adjusted_score += 2
        elif antibiotic_present and temp > 38.8:
            adjusted_score += 1

    # ── Age-based risk amplification (elderly patients deteriorate faster) ──
    if age >= 70 and adjusted_score >= 3:
        adjusted_score += 1
    elif age >= 80 and adjusted_score >= 2:
        adjusted_score += 1

    # ── Map adjusted score to label ──
    _, label = news2_risk_level(adjusted_score)
    return label
