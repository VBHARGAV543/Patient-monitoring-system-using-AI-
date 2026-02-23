"""Helper: writes the new simulate_data_*.py and train_*.py files."""
import os

BASE = os.path.dirname(__file__)

# ─────────────────────────────────────────────────────────── simulate_general ──
SIM_GENERAL = r'''"""
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
'''

# ─────────────────────────────────────────────────────── simulate_critical ──
SIM_CRITICAL = r'''"""
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
'''

# ──────────────────────────────────────────────────────────── train_general ──
TRAIN_GENERAL = r'''"""
train_general.py  — Train Random Forest on NEWS2-labelled general ward data.
Run from ML/ directory:  python train_general.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from sklearn.preprocessing import label_binarize
import joblib
import numpy as np

from simulate_data_general import simulate_general_ward, FEATURE_COLS

def main():
    print("Generating 8000 training samples...")
    records = simulate_general_ward(n_samples=8000)
    df = pd.DataFrame(records)
    print(f"Label distribution:\n{df['label'].value_counts().sort_index()}\n")

    X = df[FEATURE_COLS].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=4,
        class_weight="balanced",   # handles class imbalance
        random_state=42,
        n_jobs=-1,
    )
    print("Training (this takes ~5-10 seconds)...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\nClassification Report (0=Safe, 1=Warning, 2=Critical):")
    print(classification_report(y_test, y_pred, target_names=["Safe","Warning","Critical"]))

    cv = cross_val_score(model, X, y, cv=5, scoring="f1_macro")
    print(f"5-Fold CV F1-macro: {cv.mean():.3f} ± {cv.std():.3f}")

    # Feature importances
    importances = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x:-x[1])
    print("\nTop 10 feature importances:")
    for name, imp in importances[:10]:
        print(f"  {name:<30} {imp:.4f}")

    out_path = os.path.join(os.path.dirname(__file__), "general_model.pkl")
    joblib.dump({"model": model, "feature_cols": FEATURE_COLS}, out_path)
    print(f"\nModel saved -> {out_path}")

if __name__ == "__main__":
    main()
'''

# ──────────────────────────────────────────────────────────── train_critical ──
TRAIN_CRITICAL = r'''"""
train_critical.py  — Train Random Forest on NEWS2-labelled critical ward data.
Run from ML/ directory:  python train_critical.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import joblib

from simulate_data_critical import simulate_critical_ward, FEATURE_COLS

def main():
    print("Generating 8000 training samples...")
    records = simulate_critical_ward(n_samples=8000)
    df = pd.DataFrame(records)
    print(f"Label distribution:\n{df['label'].value_counts().sort_index()}\n")

    X = df[FEATURE_COLS].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    print("Training...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\nClassification Report (0=Safe, 1=Warning, 2=Critical):")
    print(classification_report(y_test, y_pred, target_names=["Safe","Warning","Critical"]))

    cv = cross_val_score(model, X, y, cv=5, scoring="f1_macro")
    print(f"5-Fold CV F1-macro: {cv.mean():.3f} ± {cv.std():.3f}")

    importances = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x:-x[1])
    print("\nTop 10 feature importances:")
    for name, imp in importances[:10]:
        print(f"  {name:<30} {imp:.4f}")

    out_path = os.path.join(os.path.dirname(__file__), "critical_model.pkl")
    joblib.dump({"model": model, "feature_cols": FEATURE_COLS}, out_path)
    print(f"\nModel saved -> {out_path}")

if __name__ == "__main__":
    main()
'''

files = {
    "simulate_data_general.py": SIM_GENERAL,
    "simulate_data_critical.py": SIM_CRITICAL,
    "train_general.py": TRAIN_GENERAL,
    "train_critical.py": TRAIN_CRITICAL,
}

for fname, content in files.items():
    path = os.path.join(BASE, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("All done.")
