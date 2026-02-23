"""
train_vital_estimator.py
========================
Trains regression models to estimate the 4 vitals that the hardware
cannot directly measure (BP_sys, BP_dia, RR, Glucose) from the 3 sensors
that the ESP32 + MAX30102 + DS18B20 actually provide:
    real inputs  →  HR,  SpO2,  Temp
    estimated    →  BP_sys,  BP_dia,  RR,  Glucose

These models are ONLY used in hardware mode.
Simulation mode continues to use its own full 7-vital simulation.

Training data: combined general + critical ward synthetic samples
(same MIMIC-grounded distributions used for the alarm classifier).

Run from ML/ directory:
    python train_vital_estimator.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from simulate_data_general import simulate_general_ward
from simulate_data_critical import simulate_critical_ward
from news2 import score_news2

# ────────────────────────────────────────────────────────────
# Partial NEWS2: only from the 3 real sensors
# (HR + SpO2 + Temp, max 8 out of 20)
# ────────────────────────────────────────────────────────────
def news2_partial(hr, spo2, temp):
    score = 0
    # SpO2
    if spo2 <= 91:   score += 3
    elif spo2 <= 93: score += 2
    elif spo2 <= 95: score += 1
    # HR
    if hr <= 40:     score += 3
    elif hr <= 50:   score += 1
    elif hr <= 90:   score += 0
    elif hr <= 110:  score += 1
    elif hr <= 130:  score += 2
    else:            score += 3
    # Temp
    if temp <= 35.0: score += 3
    elif temp <= 36.0: score += 1
    elif temp <= 38.0: score += 0
    elif temp <= 39.0: score += 1
    else:            score += 2
    return score


# All disease names (general + critical) for one-hot encoding
ALL_DISEASES = [
    "Hypertension", "Diabetes Type 2", "Asthma",
    "Mild Pneumonia", "UTI", "Gastroenteritis",
    "Heart Attack", "Stroke", "Severe Pneumonia",
    "Sepsis", "Acute Respiratory Failure",
]

# Features the estimator uses at inference time (available from patient DB + sensors)
ESTIMATOR_FEATURE_COLS = (
    ["HR", "SpO2", "Temp", "news2_partial", "age", "is_critical"]
    + [f"disease_{d}" for d in ALL_DISEASES]
)

# Vitals to estimate
TARGETS = ["BP_sys", "BP_dia", "RR", "Glucose"]


def build_dataset():
    print("Generating 8000 general ward samples...")
    gen_records = simulate_general_ward(n_samples=8000)
    print("Generating 8000 critical ward samples...")
    crit_records = simulate_critical_ward(n_samples=8000)

    rows = []

    for rec in gen_records:
        disease = next(
            (d for d in ALL_DISEASES if rec.get(f"disease_{d}") == 1),
            "Hypertension"   # fallback (Asthma has all zeros in general)
        )
        rows.append({
            "HR":     rec["HR"],
            "SpO2":   rec["SpO2"],
            "Temp":   rec["Temp"],
            "news2_partial": news2_partial(rec["HR"], rec["SpO2"], rec["Temp"]),
            "age":    rec["age"],
            "is_critical": 0,
            **{f"disease_{d}": int(d == disease) for d in ALL_DISEASES},
            "BP_sys":   rec["BP_sys"],
            "BP_dia":   rec["BP_dia"],
            "RR":       rec["RR"],
            "Glucose":  rec["Glucose"],
        })

    for rec in crit_records:
        disease = next(
            (d for d in ALL_DISEASES if rec.get(f"disease_{d}") == 1),
            "Sepsis"
        )
        rows.append({
            "HR":     rec["HR"],
            "SpO2":   rec["SpO2"],
            "Temp":   rec["Temp"],
            "news2_partial": news2_partial(rec["HR"], rec["SpO2"], rec["Temp"]),
            "age":    rec["age"],
            "is_critical": 1,
            **{f"disease_{d}": int(d == disease) for d in ALL_DISEASES},
            "BP_sys":   rec["BP_sys"],
            "BP_dia":   rec["BP_dia"],
            "RR":       rec["RR"],
            "Glucose":  rec["Glucose"],
        })

    return pd.DataFrame(rows)


def train_regressor(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=10,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def main():
    df = build_dataset()
    print(f"\nTotal samples: {len(df)}")

    X = df[ESTIMATOR_FEATURE_COLS].values
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

    models = {}
    print("\n── Training regressors for each estimated vital ──")
    for target in TARGETS:
        y = df[target].values
        y_train, y_test = train_test_split(y, test_size=0.2, random_state=42)

        m = train_regressor(X_train, y_train)
        y_pred = m.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        r2  = r2_score(y_test, y_pred)
        print(f"  {target:<12}  MAE={mae:6.2f}   R²={r2:.3f}")
        models[target] = m

    out_path = os.path.join(os.path.dirname(__file__), "vital_estimator.pkl")
    joblib.dump({
        "models": models,
        "feature_cols": ESTIMATOR_FEATURE_COLS,
        "targets": TARGETS,
        "all_diseases": ALL_DISEASES,
    }, out_path)
    print(f"\n✅ Saved → {out_path}")
    print("These 4 models will be used in HARDWARE MODE only.")
    print("Simulation mode is unaffected.")


if __name__ == "__main__":
    main()
