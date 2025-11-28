# train_general.py
# Script execution check
print("Script started")
import random
import pandas as pd
from simulate_data_general import simulate_general_ward
from model_general import GeneralWardModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import sys

# -------------------------------
# Generate dataset
# -------------------------------
def generate_dataset(simulations=500):
    data_rows = []
    for _ in range(simulations):
        patients = simulate_general_ward()
        for p in patients:
            # Flatten vitals into features
            vitals = p['vitals']
            row = {
                "BP_sys": vitals.get("BP_sys", 0),
                "BP_dia": vitals.get("BP_dia", 0),
                "HR": vitals.get("HR", 0),
                "Glucose": vitals.get("Glucose", 0),
                "O2": vitals.get("O2", 0),
                "Temp": vitals.get("Temp", 0),
                "nurse_nearby": int(p['nurse_nearby']),
                "disease": p['disease'],
                "alarm": p['alarm']
            }
            data_rows.append(row)
    return pd.DataFrame(data_rows)

# -------------------------------
# Preprocess dataset
# -------------------------------
def preprocess(df):
    print("✅ Preprocessing dataset...")
    # Encode categorical labels
    df['alarm_label'] = df['alarm'].map({"Safe":0, "Warning":1})
    df = pd.get_dummies(df, columns=['disease'], drop_first=True)
    X = df.drop(columns=['alarm', 'alarm_label'])
    y = df['alarm_label']
    return X, y

# -------------------------------
# Main training
# -------------------------------
def main():
    print("🚀 Generating dataset...")
    df = generate_dataset(simulations=500)

    print(f"📊 Dataset generated with {len(df)} rows")
    X, y = preprocess(df)

    print("✂️ Splitting train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Initialize and train model
    print("🤖 Training model...")
    model = GeneralWardModel()
    model.train(X_train, y_train)

    # Evaluate
    print("📈 Evaluating model...")
    y_pred = model.predict(X_test)
    print("\nClassification Report:\n")
    print(classification_report(y_test, y_pred))

    # Save model
    model.save()
    print("💾 Model saved as 'general_model.pkl'")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
