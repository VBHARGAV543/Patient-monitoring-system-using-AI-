import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ML.simulate_data_critical import simulate_critical_ward
from model_critical import CriticalWardModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# -------------------------------
# Generate dataset
# -------------------------------
def generate_dataset(simulations=500):
    data_rows = []
    for i in range(simulations):
        patients = simulate_critical_ward()
        for p in patients:
            vitals = p['vitals']
            row = {
                "BP_sys": vitals.get("BP_sys",0),
                "BP_dia": vitals.get("BP_dia",0),
                "HR": vitals.get("HR",0),
                "O2": vitals.get("O2",0),
                "Temp": vitals.get("Temp",0),
                "ECG": vitals.get("ECG",0),
                "NeurologicalScore": vitals.get("NeurologicalScore",0),
                "nurse_nearby": int(p['nurse_nearby']),
                "disease": p['disease'],
                "alarm": p['alarm']
            }
            data_rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"[INFO] Simulated {i+1}/{simulations} batches...")
    return pd.DataFrame(data_rows)

# -------------------------------
# Preprocess dataset
# -------------------------------
def preprocess(df):
    df['alarm_label'] = df['alarm'].map({"Safe":0, "Critical":1})
    df = pd.get_dummies(df, columns=['disease'], drop_first=True)
    X = df.drop(columns=['alarm','alarm_label'])
    y = df['alarm_label']
    return X, y

# -------------------------------
# Main training
# -------------------------------
if __name__ == "__main__":
    print("🚑 Generating dataset...")
    df = generate_dataset(simulations=500)
    print(f"[INFO] Dataset generated with {len(df)} records.")

    print("⚙️ Preprocessing dataset...")
    X, y = preprocess(df)

    print("📊 Splitting train/test...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CriticalWardModel()
    print("🧠 Training model...")
    model.train(X_train, y_train)

    print("🔎 Evaluating model...")
    y_pred = model.predict(X_test)
    print("\nClassification Report:\n")
    print(classification_report(y_test, y_pred))

    model.save()
    print("✅ Model saved as 'critical_model.pkl'")
