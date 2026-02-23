# 🚀 How to Restart and Test Mock Data System

## Current Status
✅ Database migration completed  
✅ Mock data code implemented  
✅ Frontend updated to display medical data  
⚠️ Backend needs restart  
⚠️ Current patient (BHARGAV) was admitted before mock data update  

## Steps to Test

### 1. Restart Backend
```powershell
cd "C:\Users\Lenovo\Desktop\ALARM FATIGUE PROTOTYPE\backend"
python main.py
```

**Expected output:**
```
✅ Critical ward model loaded successfully
✅ General ward model loaded successfully
✅ Database tables initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Open Dashboard
Go to: http://localhost:5173

### 3. Discharge Current Patient
- Click **"Discharge Patient"** button
- Confirm discharge
- This removes BHARGAV (who doesn't have mock medical data)

### 4. Admit New Patient with Mock Data
- Click **"Admit Patient"**
- Fill in:
  - **Name**: John Smith
  - **Age**: 65
  - **Problem**: Chest pain
  - **Patient Type**: CRITICAL
  - ✅ **Enable "Demo Mode"** ← IMPORTANT!
  - **Demo Scenario**: NORMAL
- Click **"Admit Patient"**

### 5. Watch the Magic! ✨

You should see:

#### Patient Info Card
- Gender: Male/Female
- Blood Type: A+, B-, O+, etc.
- Weight: 50-120 kg
- Height: 150-200 cm
- Emergency Contact with phone

#### Medical History Section (3 Cards)
**Medical History:**
- Hypertension
- Type 2 Diabetes
- Coronary Artery Disease
- Chronic Kidney Disease
- Hyperlipidemia
(and more)

**Allergies (Red Warning Card):**
- Penicillin
- Latex
- Sulfa drugs

**Current Medications:**
- Metformin 500mg - Twice daily
- Lisinopril 10mg - Once daily
- Atorvastatin 20mg - Once daily
(with dosages and frequencies)

#### Vital Signs (Updates Every 8 Seconds)
- Heart Rate: 60-180 bpm
- SpO2: 70-100%
- Temperature: 35-40°C
- BP Systolic: 80-180 mmHg
- BP Diastolic: 50-110 mmHg
- Blood Glucose: 40-300 mg/dL

#### Real-time Updates
- Watch vitals change every 8 seconds
- ML predictions appear
- Alarms trigger when vitals are critical

## Testing Different Scenarios

### Test Critical Emergency
1. Go to admission page
2. Admit patient with **Demo Scenario**: CRITICAL_EMERGENCY
3. Watch dashboard show critically abnormal vitals
4. Alarms should trigger immediately

### Test Manual Simulation
Use API to trigger specific scenarios:
```bash
# Trigger critical emergency for patient ID 5
curl -X POST "http://localhost:8000/api/patient/5/vitals/simulate?scenario=CRITICAL_EMERGENCY"
```

Available scenarios:
- `NORMAL` - Stable vitals
- `MILD_DETERIORATION` - Slight abnormalities
- `CRITICAL_EMERGENCY` - Severe abnormalities
- `FALSE_POSITIVE` - Borderline readings

## Troubleshooting

### Backend won't start
**Check:**
- Supabase credentials in `backend/database.py`
- Migration was run in Supabase
- Python dependencies installed: `pip install -r requirements.txt`

### No medical data showing
**Check:**
- Demo Mode checkbox was enabled
- Database migration was run successfully
- Patient was admitted AFTER restarting backend
- Browser cache cleared (Ctrl+Shift+R)

### Vitals not updating
**Check:**
- Backend console for errors
- WebSocket connection status in browser console
- Patient status is ACTIVE

### WebSocket keeps disconnecting
This is normal during development. As long as data appears, it's working!

## Quick Commands

**Start Backend:**
```powershell
cd backend
python main.py
```

**Start Frontend:**
```powershell
cd frontend_new
npm run dev
```

**Check API:**
```powershell
# Test if backend is running
curl http://localhost:8000/

# Get active patient
curl http://localhost:8000/api/patient/active

# Get patient vitals
curl http://localhost:8000/api/patient/4/vitals
```

## Success Checklist

After following steps above, you should have:
- ✅ Patient with complete medical profile
- ✅ Medical history displayed (conditions, allergies, meds)
- ✅ Vital signs updating every 8 seconds
- ✅ ML predictions showing
- ✅ Alarms triggering on critical vitals
- ✅ Emergency contact displayed

Enjoy your fully mocked medical monitoring system! 🏥✨
