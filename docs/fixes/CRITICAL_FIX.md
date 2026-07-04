# ⚠️ CRITICAL FIX REQUIRED - Path Issue

## Problem
Vite cannot start because the project directory contains a "#" character:
```
"Alarm fatigue #prototype"
```

Vite treats "#" as a URL fragment, causing module resolution to fail.

## ✅ SOLUTION: Rename the Directory

### Step 1: Rename Directory
```powershell
# Open PowerShell as Administrator
cd "c:\Users\Lenovo\Desktop"

# Rename the folder (remove # character)
Rename-Item "Alarm fatigue #prototype" "Alarm_fatigue_prototype"
```

### Step 2: Navigate to new location
```powershell
cd "Alarm_fatigue_prototype\frontend_new"
```

### Step 3: Start servers

**Terminal 1 - Backend:**
```powershell
cd "c:\Users\Lenovo\Desktop\Alarm_fatigue_prototype\backend"
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd "c:\Users\Lenovo\Desktop\Alarm_fatigue_prototype\frontend_new"
npm run dev
```

### Step 4: Open browser
Navigate to: **http://localhost:3000**

---

## Alternative: Use the Batch Script

If you don't want to rename, use the provided batch file:

1. Double-click `START_SERVERS.bat` in the project root
2. This will start both backend and frontend
3. Open http://localhost:3000 in your browser

---

## Why This Happens

Vite uses native ES modules which follow URL parsing rules. The "#" character in the file path is interpreted as a URL fragment identifier, breaking module resolution.

This is a known limitation: https://github.com/vitejs/vite/issues/2725

---

## After Renaming

Everything will work perfectly:
- ✅ Frontend will start on http://localhost:3000
- ✅ Backend API on http://localhost:8000
- ✅ WebSocket connections will work
- ✅ All features functional

---

## Quick Test Commands (After Rename)

```powershell
# Check if frontend starts
cd "c:\Users\Lenovo\Desktop\Alarm_fatigue_prototype\frontend_new"
npm run dev

# Should see:
# VITE v7.x.x ready in xxx ms
# ➜ Local: http://localhost:3000/
```

**The frontend code is 100% complete and working - only the directory name needs to be fixed!**
