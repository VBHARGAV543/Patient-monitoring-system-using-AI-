"""
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
