# 🚀 Mock Data System - Quick Start Guide

## Overview
Your Alarm Fatigue Prototype now includes a **complete mock data system** that generates realistic medical profiles, vital signs, and ML predictions - no hardware required!

## ⚡ Quick Setup (5 Minutes)

### Step 1: Update Database Schema
**Go to your Supabase dashboard** and run the migration:

1. Open Supabase SQL Editor
2. Copy content from `backend/migration_add_medical_fields.sql`
3. Paste and click "Run"
4. Wait for success message

### Step 2: Start Backend
```bash
cd backend
python main.py
```

You should see:
```
✅ Critical ward model loaded successfully
✅ General ward model loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend
```bash
cd frontend_new
npm run dev
```

Access at: http://localhost:5173

### Step 4: Test Mock Data
1. Click "Admit Patient"
2. Fill in:
   - Name: "John Doe"
   - Age: 65
   - Problem: "Chest pain"
   - Patient Type: "CRITICAL"
   - ✅ **Enable Demo Mode** (important!)
3. Click "Admit Patient"

## 🎯 What You'll See

### Dashboard Will Show:
1. **Patient Info Card**
   - Name, age, gender, blood type
   - Weight, height, emergency contact
   
2. **Medical History Section** (3 cards)
   - Medical conditions (e.g., "Hypertension", "Diabetes")
   - Allergies with red warning style
   - Current medications with dosages

3. **Vital Signs Cards** (updating every 8 seconds)
   - Heart Rate, SpO2, Temperature
   - Blood Pressure (Systolic/Diastolic)
   - Blood Glucose, Respiratory Rate

4. **Real-time Updates**
   - Vital signs change realistically
   - ML predictions appear
   - Alarms trigger when vitals critical

## 🔍 Features to Explore

### 1. Automatic Vital Generation
- Vitals generate every 8 seconds
- Realistic progressions (not random jumps)
- Different scenarios: normal, deteriorating, critical

### 2. Medical Profile
- Complete patient history
- Allergy warnings
- Medication lists

### 3. Vital History API
```bash
# Get vital signs history
curl http://localhost:8000/api/patient/1/vitals

# Get latest vitals
curl http://localhost:8000/api/patient/1/vitals/latest
```

### 4. Manual Simulation
```bash
# Trigger specific scenario
curl -X POST "http://localhost:8000/api/patient/1/vitals/simulate?scenario=CRITICAL_EMERGENCY"
```

Available scenarios:
- `NORMAL` - Stable vitals
- `MILD_DETERIORATION` - Slight abnormalities
- `CRITICAL_EMERGENCY` - Severe abnormalities
- `FALSE_POSITIVE` - Borderline readings

### 5. WebSocket Updates
Open browser console to see real-time messages:
```javascript
{
  "event": "vital_signs_update",
  "patient_id": 1,
  "patient_name": "John Doe",
  "vitals": { "heart_rate": 78, "spo2": 96, ... },
  "ml_prediction": { "prediction": 0, "confidence": 0.92, ... }
}
```

## 📊 API Endpoints

### Patient Management
```
POST   /api/patient/admit          # Admit with mock profile
GET    /api/patient/active         # Get active patient
POST   /api/patient/discharge/{id} # Discharge patient
GET    /api/patients/discharged    # View history
```

### Vital Signs (NEW!)
```
GET    /api/patient/{id}/vitals           # Get history
GET    /api/patient/{id}/vitals/latest    # Get latest
POST   /api/patient/{id}/vitals/simulate  # Manual trigger
```

### Testing
```
GET    /                           # API info
GET    /docs                       # Interactive API docs
```

## 🧪 Testing Scenarios

### Test 1: Normal Patient
1. Admit patient with demo mode
2. Watch vitals stay stable
3. ML prediction should be 0 (no alarm)

### Test 2: Critical Patient
1. Use manual simulation: `scenario=CRITICAL_EMERGENCY`
2. Watch vitals deteriorate
3. ML prediction should be 1 (alarm)
4. Alarm should appear on dashboard

### Test 3: Multiple Admissions
1. Admit patient → observe vitals
2. Discharge patient
3. Admit new patient → different medical profile
4. Check Records page for history

## 🎨 Mock Data Details

### Generated Patient Profile Includes:
- **Demographics**: Gender, blood type
- **Physical**: Weight (50-120 kg), Height (150-200 cm)
- **Medical History**: 5-10 realistic conditions
  - Examples: Hypertension, Diabetes, CAD, COPD, CKD
- **Allergies**: 0-3 items (30% have allergies)
  - Examples: Penicillin, Latex, Sulfa drugs
- **Medications**: 3-8 current meds
  - Includes: name, dosage, frequency
  - Example: "Metformin 500mg - Twice daily"
- **Emergency Contact**: Name and phone

### Generated Vital Signs:
- **Heart Rate**: 60-100 bpm (normal), 40-180 bpm (critical)
- **SpO2**: 95-100% (normal), 70-94% (critical)
- **Temperature**: 36.5-37.5°C (normal), 35-40°C (critical)
- **BP Systolic**: 110-130 (normal), 80-180 (critical)
- **BP Diastolic**: 70-85 (normal), 50-110 (critical)
- **Respiratory Rate**: 12-20 (normal), 8-35 (critical)
- **Blood Glucose**: 80-120 (normal), 40-300 (critical)

### ML Prediction Includes:
- **Prediction**: 0 (normal) or 1 (alarm)
- **Confidence**: 0.0-1.0 (how certain the model is)
- **Risk Score**: 0-10 scale
- **Risk Factors**: List of abnormal vitals
- **Recommendation**: Action to take

## 📝 Example Generated Data

### Patient Profile
```json
{
  "name": "John Doe",
  "age": 65,
  "gender": "Male",
  "blood_type": "A+",
  "weight": 78.5,
  "height": 175,
  "medical_history": [
    "Hypertension",
    "Type 2 Diabetes",
    "Coronary Artery Disease"
  ],
  "allergies": ["Penicillin"],
  "current_medications": [
    {
      "name": "Metformin",
      "dosage": "500mg",
      "frequency": "Twice daily"
    }
  ],
  "emergency_contact": "Jane Doe (Spouse)",
  "emergency_phone": "555-123-4567"
}
```

### Vital Signs
```json
{
  "heart_rate": 78,
  "spo2": 96,
  "temperature": 37.2,
  "bp_systolic": 125,
  "bp_diastolic": 82,
  "respiratory_rate": 16,
  "blood_glucose": 105
}
```

## 🐛 Troubleshooting

### "Column p.gender does not exist"
**Fix**: Run the database migration script in Supabase

### Vitals not updating
**Check**:
1. Demo mode enabled when admitting?
2. Backend console for errors?
3. WebSocket connected? (see connection status)

### Medical data not showing
**Check**:
1. Database migration completed?
2. Frontend updated? (Ctrl+Shift+R to refresh)
3. Patient admitted with demo_mode=true?

### Backend errors
**Check**:
1. Supabase credentials in `backend/database.py`
2. ML models exist in `ML/` folder?
3. Python dependencies installed? (`pip install -r requirements.txt`)

## 📚 Documentation

- **`MOCK_DATA_IMPLEMENTATION.md`** - Complete technical documentation
- **`backend/DATABASE_MIGRATION.md`** - Database update guide
- **`backend/database_schema.sql`** - Full schema reference
- **`backend/mock_data.py`** - Mock data generator code

## 🎉 Success Checklist

After setup, you should have:
- ✅ Backend running on port 8000
- ✅ Frontend running on port 5173
- ✅ Database has medical fields
- ✅ Patient admits with demo mode
- ✅ Medical history displays on dashboard
- ✅ Vital signs update every 8 seconds
- ✅ ML predictions appear
- ✅ Alarms trigger on critical vitals
- ✅ WebSocket shows real-time updates

## 🚀 Next Steps

1. **Test different scenarios** using manual simulation
2. **Review vital history** via API
3. **Discharge and admit** multiple patients
4. **Check Records page** for history
5. **Customize mock data** in `backend/mock_data.py`

## 💡 Tips

- **Use critical patients** for more dramatic vital changes
- **Enable browser console** to see WebSocket messages
- **Check `/docs`** for interactive API testing
- **Use different scenarios** to test alarm logic
- **Monitor backend logs** for detailed info

Enjoy your mock medical monitoring system! 🏥✨
