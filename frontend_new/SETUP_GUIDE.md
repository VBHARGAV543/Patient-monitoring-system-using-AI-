# 🚀 Frontend Setup and Deployment Guide

## Complete Implementation Summary

The frontend has been fully implemented with all REST endpoints and WebSocket connections integrated. Here's what was built:

### ✅ Completed Features

1. **Project Structure**
   - ✅ React 19 + Vite setup
   - ✅ Material-UI v7 with custom theme
   - ✅ Framer Motion animations
   - ✅ Zustand state management
   - ✅ React Router v7 navigation
   - ✅ React Query for server state
   - ✅ React Hook Form + Zod validation

2. **API Integration** (`src/services/api.js`)
   - ✅ All patient management endpoints
   - ✅ Nurse proximity endpoints
   - ✅ Sensor data endpoint
   - ✅ Health check endpoint
   - ✅ Axios interceptors for logging

3. **WebSocket Integration** (`src/hooks/useWebSocket.js`)
   - ✅ Custom WebSocket hook with auto-reconnect
   - ✅ Dashboard WebSocket (`/ws`)
   - ✅ Nurse WebSocket (`/ws/nurse/{sessionId}`)
   - ✅ Event-based message handling

4. **Pages**
   - ✅ Home page with navigation cards
   - ✅ Patient Admission form with validation
   - ✅ Real-time Dashboard with vital signs
   - ✅ Alarm status display with animations
   - ✅ Patient discharge functionality

5. **Components**
   - ✅ ConnectionStatus indicator
   - ✅ AlarmHistoryModal with charts
   - ✅ CameraView with ward-specific logic
   - ✅ VitalCard component

6. **State Management** (`src/stores/patientStore.js`)
   - ✅ Global patient state
   - ✅ Vital signs state
   - ✅ Alarm status state
   - ✅ Connection status
   - ✅ Alarm history cache

7. **Utilities** (`src/utils/helpers.js`)
   - ✅ Date/time formatting
   - ✅ Vital signs validation
   - ✅ Color coding helpers
   - ✅ Form validation
   - ✅ Demo data generation

## 🎯 How to Run

### Step 1: Start Backend
```bash
# Navigate to backend folder
cd "c:\Users\Lenovo\Desktop\Alarm fatigue #prototype\backend"

# Activate Python environment (if using venv)
# .\venv\Scripts\Activate.ps1

# Run backend server
python main.py
```

Backend should start on `http://localhost:8000`

### Step 2: Start Frontend
```bash
# Navigate to frontend_new folder
cd "c:\Users\Lenovo\Desktop\Alarm fatigue #prototype\frontend_new"

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will start on `http://localhost:3000`

### Step 3: Open Browser
Navigate to `http://localhost:3000`

## 📱 User Flow

### Scenario 1: Admit New Patient
1. Go to Home (`/`)
2. Click "Admit Patient"
3. Fill form:
   - Name: "John Doe"
   - Age: 45
   - Problem: "Pneumonia"
   - Patient Type: General/Critical
   - Optional: Enable Demo Mode
4. Wait for band availability (green status)
5. Click "Admit Patient"
6. Auto-redirects to Dashboard

### Scenario 2: Monitor Patient
1. Dashboard loads active patient
2. WebSocket connects automatically
3. Vital signs update in real-time (when sensor sends data)
4. Alarm status shows with animations
5. Click "Alarm History" to view past events
6. Toggle between table and chart views

### Scenario 3: Discharge Patient
1. On Dashboard, click "Discharge Patient"
2. Confirm in dialog
3. Patient cleared, band released
4. Can admit new patient

## 🧪 Testing Without Hardware

### Use Demo Mode:
1. When admitting patient, check "Enable Demo Mode"
2. Select scenario:
   - **NORMAL**: All vitals normal
   - **MILD_DETERIORATION**: Slightly abnormal
   - **CRITICAL_EMERGENCY**: Severe abnormal
   - **FALSE_POSITIVE**: Edge case vitals

3. Backend will tamper sensor data to simulate scenarios

### Manual Sensor Data (Optional):
Use API testing tool (Postman/Thunder Client) to POST sensor data:

```json
POST http://localhost:8000/api/sensor-data
Content-Type: application/json

{
  "band_id": "BAND_01",
  "HR": 85,
  "SpO2": 96,
  "Temp": 37.2,
  "demo_mode": false
}
```

Dashboard will update in real-time via WebSocket!

## 🔌 API Endpoints Reference

### Connected Endpoints:

**Patient Management:**
- `POST /api/patient/admit` ✅
- `POST /api/patient/discharge/{id}` ✅
- `GET /api/patient/active` ✅
- `GET /api/patient/{id}/alarm-history` ✅

**Nurse Proximity:**
- `POST /api/nurse/register` ✅ (implemented but not UI exposed yet)
- `POST /api/nurse/proximity` ✅
- `GET /api/nurse/status/{session_id}` ✅

**Sensor & Health:**
- `POST /api/sensor-data` ✅
- `GET /` ✅

**WebSockets:**
- `ws://localhost:8000/ws` ✅ (Dashboard)
- `ws://localhost:8000/ws/nurse/{sessionId}` ✅ (prepared)

## 🎨 UI Components

### Material-UI Components Used:
- AppBar, Drawer (ready for multi-page layout)
- Paper, Card (containers)
- TextField, Select, Radio, Checkbox (forms)
- Button, IconButton, Chip (actions)
- Table, TableContainer (alarm history)
- Dialog, Modal (confirmations)
- Alert, CircularProgress (feedback)
- Grid, Box, Container (layout)

### Framer Motion Animations:
- Page entrance animations
- Alarm status banner (AnimatePresence)
- Card hover effects
- Smooth transitions

### Icons (@mui/icons-material):
- Favorite (heart rate)
- Opacity (SpO2)
- Thermostat (temperature)
- BloodPressure (BP)
- LocalHospital (glucose/medical)
- Sensors (alarms)
- Person (patient)
- ExitToApp (discharge)
- History (alarm history)
- Videocam (camera)
- Wifi, Cloud (connection status)

## 📊 Data Visualization

**Recharts Integration:**
- Line charts for vital trends (HR, SpO2, Temp, BP)
- X-axis: timestamps
- Y-axis: vital values with appropriate domains
- Last 50 readings displayed
- Responsive container

## 🔧 Configuration Files

### `.env`
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### `vite.config.js`
- Proxy configured for `/api` and `/ws`
- Development server on port 3000

### `package.json`
- All dependencies installed
- Scripts: dev, build, preview, lint

## 🐛 Troubleshooting

### Issue: WebSocket not connecting
**Solution:**
1. Ensure backend is running
2. Check browser console for errors
3. Verify `ws://localhost:8000/ws` is accessible
4. Try manual reconnect button

### Issue: Band always showing "Occupied"
**Solution:**
1. Go to Dashboard
2. Discharge current patient
3. Wait 5 seconds for status update
4. Return to Admission page

### Issue: No sensor data appearing
**Solution:**
1. Check if patient is admitted
2. Verify WebSocket is connected (green chip top-right)
3. Send test sensor data via API
4. Check backend console for errors

### Issue: Alarm history empty
**Solution:**
- No sensor data has been sent yet
- Wait for ESP32 to send data, or
- Use POST /api/sensor-data to simulate

### Issue: Camera not working
**Solution:**
1. Allow camera permissions in browser
2. Check browser console for errors
3. Ensure HTTPS (or localhost for dev)

## 📦 Production Build

```bash
# Build for production
npm run build

# Output in: frontend_new/dist/

# Test production build locally
npm run preview
```

Deploy `dist/` folder to:
- Vercel
- Netlify
- GitHub Pages
- Any static hosting

**Important:** Update `.env` with production backend URL!

## 🔐 Security Notes

- No authentication implemented (add JWT/OAuth as needed)
- CORS enabled on backend for all origins (restrict in production)
- WebSocket has no auth (add token-based auth)
- Demo mode exposes backend tampering (disable in production)

## 📈 Future Enhancements

Possible additions:
1. **Multi-patient support** (when more bands available)
2. **Nurse mobile view** (separate page for proximity alerts)
3. **Historical data charts** (extended time periods)
4. **Export alarm reports** (PDF/CSV)
5. **User authentication** (role-based access)
6. **Push notifications** (browser notifications API)
7. **Dark mode toggle**
8. **Accessibility improvements** (ARIA labels, keyboard nav)

## ✅ Verification Checklist

Before deployment:
- [ ] Backend running on port 8000
- [ ] ML models loaded (critical_model.pkl, general_model.pkl)
- [ ] Database connected (Supabase/PostgreSQL)
- [ ] Frontend dev server starts without errors
- [ ] Can admit patient successfully
- [ ] Dashboard loads active patient
- [ ] WebSocket connects (green status)
- [ ] Sensor data updates vitals in real-time
- [ ] Alarm history modal opens
- [ ] Can discharge patient
- [ ] Camera activates (with permissions)

## 🎉 Success!

Your modern frontend is now fully connected to the backend with:
- ✅ All REST endpoints integrated
- ✅ WebSocket real-time updates
- ✅ Material-UI professional design
- ✅ Framer Motion animations
- ✅ State management with Zustand
- ✅ Form validation with Zod
- ✅ Data visualization with Recharts
- ✅ Responsive mobile-friendly layout

**Next Steps:**
1. Start both backend and frontend
2. Admit a patient
3. Send sensor data (hardware or API)
4. Watch real-time monitoring in action!

---

**Questions or Issues?**
Check browser console (F12) and backend terminal for detailed logs.
