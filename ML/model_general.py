# model_general.py
import joblib
from sklearn.ensemble import RandomForestClassifier

class GeneralWardModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=50, 
            random_state=42,
            n_jobs=-1
        )

    def train(self, X, y):
        print(f"[INFO] Training RandomForest on {len(X)} samples with {X.shape[1]} features...")
        self.model.fit(X, y)
        print("[INFO] Training complete ✅")

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path="general_model.pkl"):
        joblib.dump(self.model, path)
        print(f"[INFO] Model saved at {path}")

    def load(self, path="general_model.pkl"):
        self.model = joblib.load(path)
        print(f"[INFO] Model loaded from {path}")
