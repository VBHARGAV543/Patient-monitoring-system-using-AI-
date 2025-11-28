# simulate_data_general.py
import random

# -------------------------------
# Diseases and real drugs
# -------------------------------
diseases = ["Hypertension", "Diabetes", "Asthma", "Mild Pneumonia"]

medications = {
    "Hypertension": ["Amlodipine", "Losartan", "Hydrochlorothiazide"],
    "Diabetes": ["Metformin", "Glipizide", "Insulin"],
    "Asthma": ["Salbutamol", "Budesonide", "Montelukast"],
    "Mild Pneumonia": ["Azithromycin", "Amoxicillin", "Levofloxacin"]
}

# -------------------------------
# Patients
# -------------------------------
patients = [
    {"name": "John Doe", "age": 45, "allergies": ["Amlodipine"]},
    {"name": "Mary Ann", "age": 60, "allergies": []},
    {"name": "Alex Smith", "age": 32, "allergies": ["Insulin"]},
    {"name": "Priya Kaur", "age": 55, "allergies": []},
    {"name": "David Li", "age": 40, "allergies": ["Salbutamol"]}
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
    # Base vitals by disease
    if disease == "Hypertension":
        vitals["BP_sys"] = random.randint(130, 160)
        vitals["BP_dia"] = random.randint(80, 100)
        vitals["HR"] = random.randint(60, 100)
    elif disease == "Diabetes":
        vitals["Glucose"] = random.randint(140, 220)
        vitals["HR"] = random.randint(60, 100)
    elif disease == "Asthma":
        vitals["O2"] = random.randint(85, 95)
        vitals["HR"] = random.randint(70, 110)
    elif disease == "Mild Pneumonia":
        vitals["Temp"] = random.randint(37, 39)
        vitals["O2"] = random.randint(88, 95)
        vitals["HR"] = random.randint(70, 100)

    # Drug effects (simplified)
    if disease == "Hypertension":
        vitals["BP_sys"] -= random.randint(5, 10) if drug in medications[disease] else 0
        vitals["BP_dia"] -= random.randint(3, 7) if drug in medications[disease] else 0
    if disease == "Diabetes":
        vitals["Glucose"] -= random.randint(10, 30) if drug in medications[disease] else 0
    if disease == "Asthma":
        vitals["O2"] += random.randint(2, 5) if drug in medications[disease] else 0
    if disease == "Mild Pneumonia":
        vitals["Temp"] -= random.randint(1, 2) if drug in medications[disease] else 0
        vitals["O2"] += random.randint(1, 3) if drug in medications[disease] else 0

    return vitals

def determine_alarm(vitals, disease):
    alarm = "Safe"
    if disease == "Hypertension" and (vitals["BP_sys"] > 155 or vitals["BP_dia"] > 95):
        alarm = "Warning"
    if disease == "Diabetes" and vitals["Glucose"] > 200:
        alarm = "Warning"
    if disease == "Asthma" and vitals["O2"] < 88:
        alarm = "Warning"
    if disease == "Mild Pneumonia" and (vitals.get("Temp",0) > 38.5 or vitals.get("O2",0) < 88):
        alarm = "Warning"
    return alarm

# -------------------------------
# Main simulation function
# -------------------------------
def simulate_general_ward():
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
    data = simulate_general_ward()
    for p in data:
        print(p)
