import requests
import time

BASE_URL = 'http://localhost:8000'

patients = [
    {'name': 'John Smith', 'age': 45, 'problem': 'Chest Pain'},
    {'name': 'Emma Johnson', 'age': 32, 'problem': 'Fever'},
    {'name': 'Michael Brown', 'age': 58, 'problem': 'Headache'},
    {'name': 'Sophia Davis', 'age': 28, 'problem': 'Stomach Ache'},
    {'name': 'William Wilson', 'age': 41, 'problem': 'Back Pain'},
    {'name': 'Olivia Taylor', 'age': 36, 'problem': 'Cough'},
    {'name': 'James Martinez', 'age': 52, 'problem': 'Fatigue'},
    {'name': 'Ava Anderson', 'age': 29, 'problem': 'Nausea'},
    {'name': 'Robert Lee', 'age': 48, 'problem': 'Dizziness'}
]

print('Adding 9 GENERAL ward patients...\n')

for p in patients:
    try:
        # Admit patient
        r = requests.post(
            f'{BASE_URL}/api/patient/admit',
            json={
                'name': p['name'],
                'age': p['age'],
                'problem': p['problem'],
                'patient_type': 'GENERAL',
                'demo_mode': True,
                'demo_scenario': 'NORMAL'
            }
        )
        
        if r.status_code == 200:
            pid = r.json()['id']
            print(f'✅ Admitted: {p["name"]} (ID: {pid})')
            
            # Wait a bit before discharging
            time.sleep(1)
            
            # Discharge patient
            rd = requests.post(f'{BASE_URL}/api/patient/discharge/{pid}')
            if rd.status_code == 200:
                print(f'✅ Discharged: {p["name"]}\n')
            else:
                print(f'⚠️  Could not discharge: {p["name"]}\n')
        else:
            print(f'❌ Failed to admit: {p["name"]} - {r.text}\n')
            
    except Exception as e:
        print(f'❌ Error for {p["name"]}: {e}\n')
    
    time.sleep(0.5)

print('\n✅ Done! All 9 GENERAL ward patients have been added to the records.')
