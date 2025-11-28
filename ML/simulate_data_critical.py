import random

# -------------------------------
# Diseases and real drugs for critical ward
# -------------------------------
diseases = ["Heart Attack", "Stroke", "Severe Pneumonia", "Sepsis"]

medications = {
    "Heart Attack": ["Aspirin", "Clopidogrel", "Heparin"],
    "Stroke": ["Alteplase", "Aspirin", "Clopidogrel"],
    "Severe Pneumonia": ["Meropenem", "Ceftriaxone", "Levofloxacin"],
    "Sepsis": ["Vancomycin", "Meropenem", "Piperacillin-Tazobactam"]
}

# -------------------------------
# Patients
# -------------------------------
patients = [
    {"name": "Ravi Kumar", "age": 65, "allergies": ["Aspirin"]},
    {"name": "Linda Wong", "age": 70, "allergies": []},
    {"name": "Mark Johnson", "age": 55, "allergies": ["Meropenem"]},
    {"name": "Sara Lee", "age": 60, "allergies": []},
    {"name": "Tom Hardy", "age": 50, "allergies": ["Heparin"]}
]

# -------------------------------
# Helper functions
# -------------------------------
def select_disease():
    return random.choice(diseases)

def assign_drug(disease, allergies):
    valid_drugs = [d for d in medications[disease] if d not in allergies]
    return random.choice(valid_drugs)

def generate_vitals(disease, drug):
    vitals = {}
    if disease == "Heart Attack":
        vitals["BP_sys"] = random.randint(100, 160)
        vitals["BP_dia"] = random.randint(60, 100)
        vitals["HR"] = random.randint(70, 120)
        vitals["ECG"] = random.choice([0,1])  # 0=normal, 1=abnormal
    elif disease == "Stroke":
        vitals["BP_sys"] = random.randint(120, 180)
        vitals["BP_dia"] = random.randint(70, 110)
        vitals["HR"] = random.randint(60, 110)
        vitals["NeurologicalScore"] = random.randint(0, 15)
    elif disease == "Severe Pneumonia":
        vitals["Temp"] = random.randint(38, 41)
        vitals["O2"] = random.randint(80, 92)
        vitals["HR"] = random.randint(80, 120)
    elif disease == "Sepsis":
        vitals["Temp"] = random.randint(38, 41)
        vitals["BP_sys"] = random.randint(80, 120)
        vitals["BP_dia"] = random.randint(50, 80)
        vitals["HR"] = random.randint(90, 130)

    # Drug effects (simplified)
    return vitals

def determine_alarm(vitals, disease):
    alarm = "Safe"
    if disease == "Heart Attack" and (vitals["BP_sys"] < 90 or vitals["HR"] > 110 or vitals["ECG"]==1):
        alarm = "Critical"
    if disease == "Stroke" and (vitals["BP_sys"] > 170 or vitals.get("NeurologicalScore", 15) < 8):
        alarm = "Critical"
    if disease == "Severe Pneumonia" and (vitals.get("O2",100) < 85 or vitals.get("Temp",37) > 40):
        alarm = "Critical"
    if disease == "Sepsis" and (vitals.get("BP_sys",100) < 85 or vitals.get("Temp",37) > 40 or vitals["HR"] > 120):
        alarm = "Critical"
    return alarm

# -------------------------------
# Main simulation function
# -------------------------------
def simulate_critical_ward():
    results = []
    for patient in patients:
        disease = select_disease()
        drug = assign_drug(disease, patient["allergies"])
        vitals = generate_vitals(disease, drug)
        alarm_status = determine_alarm(vitals, disease)
        nurse_nearby = random.choice([True, False])

        results.append({
            "patient": patient['name'],
            "age": patient['age'],
            "disease": disease,
            "drug": drug,
            "vitals": vitals,
            "alarm": alarm_status,
            "nurse_nearby": nurse_nearby
        })
    return results

# -------------------------------
# For testing standalone
# -------------------------------
if __name__ == "__main__":
    data = simulate_critical_ward()
    for p in data:
        print(p)
