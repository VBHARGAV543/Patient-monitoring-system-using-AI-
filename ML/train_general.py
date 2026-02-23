"""
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
