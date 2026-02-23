"""
simulate_data_critical.py  — MIMIC-grounded + NEWS2-labelled training data.
"""
import random
from news2 import score_news2, profile_adjusted_label

DISEASE_PROFILES = {
    "Heart Attack": {
        "vitals": {"HR":(108,20),"SpO2":(93,4),"Temp":(37.1,0.5),"BP_sys":(95,22),"BP_dia":(62,14),"RR":(22,5),"Glucose":(145,40),"ECG":(0.7,0.3),"neuro":(14,1)},
        "medications": [
            {"name":"Aspirin 300mg",    "effects":{}},
            {"name":"Clopidogrel 75mg", "effects":{}},
            {"name":"Heparin IV",       "effects":{}},
            {"name":"Nitroglycerin IV", "effects":{"BP_sys":-12,"HR":5}},
        ],
        "allergies_pool": ["Aspirin 300mg","Heparin IV"],
    },
    "Stroke": {
        "vitals": {"HR":(88,16),"SpO2":(94,3.5),"Temp":(37.4,0.6),"BP_sys":(165,25),"BP_dia":(100,16),"RR":(20,4),"Glucose":(138,35),"ECG":(0.3,0.3),"neuro":(8,4)},
        "medications": [
            {"name":"Alteplase IV",    "effects":{}},
            {"name":"Aspirin 100mg",   "effects":{}},
            {"name":"Labetalol IV",    "effects":{"BP_sys":-20,"BP_dia":-12}},
        ],
        "allergies_pool": ["Aspirin 100mg"],
    },
    "Severe Pneumonia": {
        "vitals": {"HR":(108,18),"SpO2":(86,5),"Temp":(39.5,0.9),"BP_sys":(108,18),"BP_dia":(66,12),"RR":(30,7),"Glucose":(125,30),"ECG":(0.2,0.2),"neuro":(12,3)},
        "medications": [
            {"name":"Meropenem 1g IV",           "effects":{"Temp":-1.2,"HR":-8,"RR":-4}},
            {"name":"Ceftriaxone 2g IV",          "effects":{"Temp":-1.0,"HR":-6,"RR":-3}},
            {"name":"Piperacillin-Tazobactam IV", "effects":{"Temp":-1.0,"RR":-3}},
        ],
        "allergies_pool": ["Meropenem 1g IV"],
    },
    "Sepsis": {
        "vitals": {"HR":(118,18),"SpO2":(90,5),"Temp":(39.2,1.2),"BP_sys":(82,18),"BP_dia":(52,12),"RR":(28,6),"Glucose":(148,45),"ECG":(0.3,0.3),"neuro":(11,4)},
        "medications": [
            {"name":"Vancomycin 1g IV",           "effects":{"Temp":-1.0,"HR":-6}},
            {"name":"Meropenem 1g IV",            "effects":{"Temp":-1.2,"HR":-8}},
            {"name":"Norepinephrine IV",           "effects":{"BP_sys":25,"BP_dia":12}},
        ],
        "allergies_pool": ["Vancomycin 1g IV","Meropenem 1g IV"],
    },
    "Acute Respiratory Failure": {
        "vitals": {"HR":(112,18),"SpO2":(84,6),"Temp":(37.8,0.8),"BP_sys":(105,20),"BP_dia":(65,12),"RR":(32,8),"Glucose":(118,25),"ECG":(0.4,0.3),"neuro":(12,3)},
        "medications": [
            {"name":"Oxygen therapy",   "effects":{"SpO2":8,"RR":-5}},
            {"name":"Dexamethasone IV", "effects":{"RR":-3}},
        ],
        "allergies_pool": [],
    },
}

PATIENT_AGES = [49, 55, 60, 65, 68, 72, 75, 80]

FEATURE_COLS = [
    "HR","SpO2","Temp","BP_sys","BP_dia","RR","Glucose",
    "ECG_abnormal","neuro_score","news2_score","age",
    "has_vasopressor","has_anticoagulant","has_antibiotic","has_bp_med","has_allergy_flag",
    "disease_Heart Attack","disease_Sepsis","disease_Severe Pneumonia","disease_Stroke",
]

def _c(v,lo,hi): return max(lo,min(hi,v))

def generate_patient_sample(disease_name, age):
    profile = DISEASE_PROFILES[disease_name]
    vitals = {}
    for k,(m,s) in profile["vitals"].items():
        if k=="ECG": vitals["ECG_abnormal"]=int(random.random()<m)
        elif k=="neuro": vitals["neuro_score"]=int(_c(round(random.gauss(m,s)),0,15))
        else: vitals[k]=round(random.gauss(m,s),1)
    for k,lo,hi in [("HR",25,220),("SpO2",60,100),("Temp",34.0,42.0),
                     ("BP_sys",50,250),("BP_dia",25,150),("RR",4,60),("Glucose",40,600)]:
        vitals[k]=_c(vitals[k],lo,hi)

    allergies=profile["allergies_pool"]
    has_allergy=random.random()<0.15
    allergy_drug=random.choice(allergies) if has_allergy and allergies else None
    valid_meds=[m for m in profile["medications"] if allergy_drug is None or m["name"]!=allergy_drug]
    medication_names=[]
    if valid_meds and random.random()<0.78:
        n_meds=random.randint(1,min(2,len(valid_meds)))
        chosen=random.sample(valid_meds,n_meds)
        for med in chosen:
            for vk,delta in med["effects"].items():
                if vk in vitals: vitals[vk]=round(vitals[vk]+delta*random.uniform(0.6,1.1),1)
            medication_names.append(med["name"])

    for k,lo,hi in [("HR",25,220),("SpO2",60,100),("Temp",34.0,42.0),
                     ("BP_sys",50,250),("BP_dia",25,150),("RR",4,60),("Glucose",40,600)]:
        vitals[k]=_c(vitals[k],lo,hi)

    ns=score_news2(hr=vitals["HR"],spo2=vitals["SpO2"],bp_sys=vitals["BP_sys"],rr=vitals["RR"],
                   temp=vitals["Temp"],consciousness="alert" if vitals["neuro_score"]>=13 else "confused")
    label=profile_adjusted_label(base_score=ns,disease=disease_name,medications=medication_names,vitals=vitals,age=age)
    ml=[m.lower() for m in medication_names]
    return {
        "HR":vitals["HR"],"SpO2":vitals["SpO2"],"Temp":vitals["Temp"],
        "BP_sys":vitals["BP_sys"],"BP_dia":vitals["BP_dia"],"RR":vitals["RR"],"Glucose":vitals["Glucose"],
        "ECG_abnormal":vitals["ECG_abnormal"],"neuro_score":vitals["neuro_score"],
        "news2_score":ns,"age":age,
        "has_vasopressor":   int(any(k in m for m in ml for k in ["norepinephrine","vasopressin","dopamine"])),
        "has_anticoagulant": int(any(k in m for m in ml for k in ["heparin","alteplase","clopidogrel"])),
        "has_antibiotic":    int(any(k in m for m in ml for k in ["vancomycin","meropenem","ceftriaxone","piperacillin"])),
        "has_bp_med":        int(any(k in m for m in ml for k in ["labetalol","nitroglycerin","furosemide"])),
        "has_allergy_flag":  int(has_allergy),
        "disease_Heart Attack":        int(disease_name=="Heart Attack"),
        "disease_Sepsis":              int(disease_name=="Sepsis"),
        "disease_Severe Pneumonia":    int(disease_name=="Severe Pneumonia"),
        "disease_Stroke":              int(disease_name=="Stroke"),
        "label": label,
    }

def simulate_critical_ward(n_samples=5000):
    diseases=list(DISEASE_PROFILES.keys())
    records=[]
    per_disease=n_samples//len(diseases)
    for disease in diseases:
        for _ in range(per_disease):
            records.append(generate_patient_sample(disease,random.choice(PATIENT_AGES)))
    random.shuffle(records)
    return records

if __name__=="__main__":
    data=simulate_critical_ward(500)
    labels=[r["label"] for r in data]
    print(f"Generated {len(data)} | 0:{labels.count(0)} 1:{labels.count(1)} 2:{labels.count(2)}")
