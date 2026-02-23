"""
Script to add 9 dummy patients via API - All GENERAL ward
"""
import requests
import random

DUMMY_PATIENTS = [
    {"name": "John Smith", "age": 45, "gender": "Male", "problem": "Hypertension monitoring"},
    {"name": "Maria Garcia", "age": 32, "gender": "Female", "problem": "Post-surgery recovery"},
    {"name": "David Lee", "age": 58, "gender": "Male", "problem": "Diabetes management"},
    {"name": "Sarah Johnson", "age": 27, "gender": "Female", "problem": "Asthma observation"},
    {"name": "Michael Brown", "age": 41, "gender": "Male", "problem": "Cardiac checkup"},
    {"name": "Emily Davis", "age": 35, "gender": "Female", "problem": "Pneumonia treatment"},
    {"name": "James Wilson", "age": 52, "gender": "Male", "problem": "Back pain assessment"},
    {"name": "Lisa Anderson", "age": 29, "gender": "Female", "problem": "Migraine monitoring"},
    {"name": "Robert Taylor", "age": 63, "gender": "Male", "problem": "Arthritis care"}
]

API_URL = "http://localhost:8000/api/patient/admit"

def main():
    print("Adding 9 dummy patients (GENERAL ward) via API...")
    
    for i, patient in enumerate(DUMMY_PATIENTS, 1):
        payload = {
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "problem": patient["problem"],
            "patient_type": "GENERAL",
            "demo_mode": True,  # Enable vitals simulation
            "hardware_mode": False,
            "weight": 60.0 + random.randint(0, 40),
            "height": 155.0 + random.randint(0, 30),
            "medical_history": f"Previous checkups normal for {patient['name']}",
            "allergies": random.choice(["None", "Penicillin", "Peanuts", ""]),
            "current_medications": random.choice(["None", "Aspirin", "Metformin", ""]),
            "emergency_contact": f"+91 98765{43210 + i}"
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Created patient {i}/9: {patient['name']} (ID: {result['id']})")
            else:
                print(f"✗ Failed to create {patient['name']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Failed to create {patient['name']}: {e}")
    
    print("\nDone! 9 dummy patients added.")

if __name__ == "__main__":
    main()