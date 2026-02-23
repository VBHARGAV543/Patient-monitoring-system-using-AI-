"""
simulate_data_general.py  — MIMIC-grounded + NEWS2-labelled training data.
"""
import random
from news2 import score_news2, profile_adjusted_label

DISEASE_PROFILES = {
    "Hypertension": {
        "vitals": {"HR":(80,12),"SpO2":(97,1.5),"Temp":(36.8,0.3),"BP_sys":(148,18),"BP_dia":(95,10),"RR":(16,2),"Glucose":(105,15)},
        "medications": [
            {"name":"Amlodipine 5mg",    "effects":{"BP_sys":-18,"BP_dia":-10}},
            {"name":"Losartan 50mg",     "effects":{"BP_sys":-15,"BP_dia":-8}},
            {"name":"Lisinopril 10mg",   "effects":{"BP_sys":-14,"BP_dia":-8}},
            {"name":"Hydrochlorothiazide","effects":{"BP_sys":-12,"BP_dia":-7}},
            {"name":"Metoprolol 50mg",   "effects":{"BP_sys":-10,"HR":-10}},
        ],
        "allergies_pool": ["Amlodipine 5mg","Lisinopril 10mg"],
    },
    "Diabetes Type 2": {
        "vitals": {"HR":(82,13),"SpO2":(96,2),"Temp":(36.9,0.4),"BP_sys":(132,15),"BP_dia":(84,9),"RR":(17,2),"Glucose":(185,50)},
        "medications": [
            {"name":"Metformin 500mg",  "effects":{"Glucose":-45}},
            {"name":"Glipizide 5mg",    "effects":{"Glucose":-50}},
            {"name":"Insulin Regular",  "effects":{"Glucose":-70}},
            {"name":"Sitagliptin 100mg","effects":{"Glucose":-35}},
        ],
        "allergies_pool": ["Insulin Regular"],
    },
    "Asthma": {
        "vitals": {"HR":(94,14),"SpO2":(91,3.5),"Temp":(37.0,0.4),"BP_sys":(122,12),"BP_dia":(78,8),"RR":(23,5),"Glucose":(98,12)},
        "medications": [
            {"name":"Salbutamol 100mcg","effects":{"SpO2":5,"RR":-4,"HR":8}},
            {"name":"Budesonide 200mcg","effects":{"SpO2":3,"RR":-2}},
            {"name":"Montelukast 10mg", "effects":{"SpO2":2,"RR":-2}},
        ],
        "allergies_pool": ["Salbutamol 100mcg"],
    },
    "Mild Pneumonia": {
        "vitals": {"HR":(96,14),"SpO2":(92,3),"Temp":(38.6,0.7),"BP_sys":(118,14),"BP_dia":(74,9),"RR":(25,5),"Glucose":(110,20)},
        "medications": [
            {"name":"Amoxicillin 500mg", "effects":{"Temp":-0.8,"RR":-2,"HR":-5}},
            {"name":"Azithromycin 250mg","effects":{"Temp":-0.7,"RR":-2}},
            {"name":"Levofloxacin 500mg","effects":{"Temp":-1.0,"RR":-3}},
        ],
        "allergies_pool": ["Amoxicillin 500mg"],
    },
    "UTI": {
        "vitals": {"HR":(90,12),"SpO2":(97,1),"Temp":(38.0,0.6),"BP_sys":(124,14),"BP_dia":(78,8),"RR":(18,3),"Glucose":(102,14)},
        "medications": [
            {"name":"Ciprofloxacin 500mg", "effects":{"Temp":-0.6,"HR":-5}},
            {"name":"Nitrofurantoin 100mg","effects":{"Temp":-0.5}},
        ],
        "allergies_pool": ["Ciprofloxacin 500mg"],
    },
    "Gastroenteritis": {
        "vitals": {"HR":(95,14),"SpO2":(97,1),"Temp":(37.8,0.6),"BP_sys":(108,16),"BP_dia":(68,10),"RR":(18,3),"Glucose":(88,18)},
        "medications": [
            {"name":"Oral Rehydration Salts","effects":{"BP_sys":8,"HR":-8}},
            {"name":"Ondansetron 4mg",       "effects":{}},
        ],
        "allergies_pool": [],
    },
}

PATIENT_AGES = [38, 45, 52, 58, 65, 67, 72, 80]

FEATURE_COLS = [
    "HR","SpO2","Temp","BP_sys","BP_dia","RR","Glucose","news2_score","age",
    "has_bp_med","has_glucose_med","has_bronchodilator","has_antibiotic","has_allergy_flag",
    "disease_Diabetes Type 2","disease_Gastroenteritis",
    "disease_Hypertension","disease_Mild Pneumonia","disease_UTI",
]

def _c(v,lo,hi): return max(lo,min(hi,v))

def generate_patient_sample(disease_name, age):
    profile = DISEASE_PROFILES[disease_name]
    vitals = {k: round(random.gauss(m,s),1) for k,(m,s) in profile["vitals"].items()}
    for k,lo,hi in [("HR",25,200),("SpO2",70,100),("Temp",34.0,42.0),
                     ("BP_sys",60,250),("BP_dia",30,150),("RR",4,50),("Glucose",40,600)]:
        vitals[k]=_c(vitals[k],lo,hi)

    allergies = profile["allergies_pool"]
    has_allergy = random.random()<0.2
    allergy_drug = random.choice(allergies) if has_allergy and allergies else None
    valid_meds = [m for m in profile["medications"] if allergy_drug is None or m["name"]!=allergy_drug]
    medication_names = []
    if valid_meds and random.random()<0.82:
        med = random.choice(valid_meds)
        for vk,delta in med["effects"].items():
            if vk in vitals: vitals[vk]=round(vitals[vk]+delta*random.uniform(0.6,1.2),1)
        medication_names = [med["name"]]

    for k,lo,hi in [("HR",25,200),("SpO2",70,100),("Temp",34.0,42.0),
                     ("BP_sys",60,250),("BP_dia",30,150),("RR",4,50),("Glucose",40,600)]:
        vitals[k]=_c(vitals[k],lo,hi)

    ns = score_news2(hr=vitals["HR"],spo2=vitals["SpO2"],bp_sys=vitals["BP_sys"],rr=vitals["RR"],temp=vitals["Temp"])
    label = profile_adjusted_label(base_score=ns,disease=disease_name,medications=medication_names,vitals=vitals,age=age)
    ml = [m.lower() for m in medication_names]
    return {
        "HR":vitals["HR"],"SpO2":vitals["SpO2"],"Temp":vitals["Temp"],
        "BP_sys":vitals["BP_sys"],"BP_dia":vitals["BP_dia"],"RR":vitals["RR"],"Glucose":vitals["Glucose"],
        "news2_score":ns,"age":age,
        "has_bp_med":       int(any(k in m for m in ml for k in ["amlodipine","losartan","lisinopril","hydrochlorothiazide","metoprolol"])),
        "has_glucose_med":  int(any(k in m for m in ml for k in ["metformin","insulin","glipizide","sitagliptin"])),
        "has_bronchodilator":int(any(k in m for m in ml for k in ["salbutamol","budesonide","montelukast"])),
        "has_antibiotic":   int(any(k in m for m in ml for k in ["amoxicillin","azithromycin","levofloxacin","ciprofloxacin","nitrofurantoin"])),
        "has_allergy_flag": int(has_allergy),
        "disease_Diabetes Type 2":int(disease_name=="Diabetes Type 2"),
        "disease_Gastroenteritis": int(disease_name=="Gastroenteritis"),
        "disease_Hypertension":    int(disease_name=="Hypertension"),
        "disease_Mild Pneumonia":  int(disease_name=="Mild Pneumonia"),
        "disease_UTI":             int(disease_name=="UTI"),
        "label": label,
    }

def simulate_general_ward(n_samples=5000):
    diseases = list(DISEASE_PROFILES.keys())
    records = []
    per_disease = n_samples // len(diseases)
    for disease in diseases:
        for _ in range(per_disease):
            records.append(generate_patient_sample(disease, random.choice(PATIENT_AGES)))
    random.shuffle(records)
    return records

if __name__=="__main__":
    data = simulate_general_ward(600)
    labels=[r["label"] for r in data]
    print(f"Generated {len(data)} samples | 0:{labels.count(0)} 1:{labels.count(1)} 2:{labels.count(2)}")
