# Network Configuration Guide

## Current Network Setup (Updated: January 3, 2026)

### 📡 Current IP Address
- **Local IP**: `10.138.1.240`
- **Network Interface**: Wi-Fi

### 🔧 Updated Components

#### 1. Mobile App (Android)
**File**: [mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/utils/Constants.kt](mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/utils/Constants.kt)
```kotlin
const val BASE_URL = "http://10.138.1.240:8000"
const val WS_URL = "ws://10.138.1.240:8000"
```

**File**: [mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/CameraStreamActivity.kt](mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/CameraStreamActivity.kt)
```kotlin
private val STREAM_URL = "http://10.138.1.240:8000/stream"
```

#### 2. Backend Server
**File**: [backend/main.py](backend/main.py)
- Server will bind to `0.0.0.0:8000` (all interfaces)
- Accessible via `http://10.138.1.240:8000`

#### 3. Frontend Web App
**File**: [frontend_new/src/services/api.js](frontend_new/src/services/api.js)
- Uses `localhost:8000` when running on same machine
- For remote access: Set environment variable `VITE_API_URL=http://10.138.1.240:8000`

**File**: [frontend_new/src/hooks/useWebSocket.js](frontend_new/src/hooks/useWebSocket.js)
- WebSocket: `ws://localhost:8000`
- For remote access: Set environment variable `VITE_WS_URL=ws://10.138.1.240:8000`

---

## 🚀 Quick Start After Network Change

### 1. Start Backend Server
```bash
cd backend
python main.py
```
Backend will be accessible at: `http://10.138.1.240:8000`

### 2. Start Frontend (Local Machine)
```bash
cd frontend_new
npm run dev
```
Frontend: `http://localhost:3000`

### 3. Access from Mobile App
- Ensure phone is on same Wi-Fi network
- Mobile app is already configured to connect to `10.138.1.240:8000`
- Rebuild the app if changes were made to Constants.kt

---

## 🔄 What to Do When IP Changes Again

### Step 1: Find Your New IP
Run in PowerShell:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -eq "Dhcp" } | Select-Object IPAddress, InterfaceAlias
```

### Step 2: Update These Files
1. **Mobile App Constants**:
   - [mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/utils/Constants.kt](mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/utils/Constants.kt)
   - Update `BASE_URL` and `WS_URL`

2. **Camera Stream**:
   - [mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/CameraStreamActivity.kt](mobile_app/NurseAlarmApp/app/src/main/java/com/example/nursealarmapp/CameraStreamActivity.kt)
   - Update `STREAM_URL`

3. **Rebuild Android App** (in Android Studio):
   - Build → Rebuild Project
   - Run → Run 'app'

### Step 3: Verify Connection
Test backend accessibility:
```powershell
Invoke-WebRequest -Uri "http://YOUR_NEW_IP:8000/" -Method GET
```

---

## 🔍 Troubleshooting

### Mobile App Can't Connect

1. **Check same network**: Ensure phone and laptop are on the same Wi-Fi
2. **Check firewall**: Windows Firewall might block port 8000
   ```powershell
   New-NetFirewallRule -DisplayName "Patient Monitor Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```
3. **Verify backend is running**: Check if server responds at `http://10.138.1.240:8000`

### Frontend Can't Connect to Backend

1. **Check if backend is running**: Visit `http://localhost:8000` in browser
2. **CORS issues**: Backend already has CORS middleware configured
3. **Check environment variables**: Ensure `.env` file has correct URLs

### WebSocket Connection Fails

1. **Check WS URL**: Should be `ws://` not `http://`
2. **Verify backend WebSocket endpoint**: `/ws` should be available
3. **Check browser console**: Look for WebSocket connection errors

---

## 📱 Mobile App Network Requirements

### Prerequisites
- Phone and laptop on **same Wi-Fi network**
- Laptop firewall allows incoming connections on port 8000
- Backend server running on laptop

### Testing Connectivity
From your phone's browser, try accessing:
```
http://10.138.1.240:8000/
```
If you see the API documentation, the connection is working.

---

## 🌐 Environment Variables (Optional)

### Frontend (.env file in frontend_new/)
```env
VITE_API_URL=http://10.138.1.240:8000
VITE_WS_URL=ws://10.138.1.240:8000
```

Use these when accessing frontend from a different device on the network.

---

## 📝 Network History
- **Previous IP**: 10.142.10.37
- **Current IP**: 10.138.1.240
- **Last Updated**: January 3, 2026
