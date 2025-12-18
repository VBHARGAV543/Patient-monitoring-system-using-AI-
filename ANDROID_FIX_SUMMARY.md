# Android App Connectivity Fixes - Summary

## Issues Fixed

### 1. ✅ simulate_vitals_background() Now Broadcasts to Nurse Connections
**Problem:** The vital signs simulation function only broadcast to dashboard WebSocket connections (`active_connections` list), not to nurse app connections (`nurse_connections` dict).

**Solution:** Added broadcast loops to send vital updates and alarms to ALL connected nurses:
```python
# After broadcasting to dashboard, now also sends to nurses:
for session_id in list(manager.nurse_connections.keys()):
    try:
        await manager.send_to_nurse(session_id, vital_update_msg)
    except Exception as e:
        print(f"Failed to send to nurse {session_id}: {e}")
```

### 2. ✅ Added patient_type Field to WebSocket Messages
**Problem:** Android CriticalWardActivity filters messages by `patient_type == "CRITICAL"` but messages didn't include this field.

**Solution:** Added `"patient_type": patient['patient_type']` to both vital_signs_update and alarm_triggered messages.

### 3. ✅ nurse_sessions Table Already Exists
**Status:** The nurse_sessions table schema was already defined in database.py and is created automatically on startup via `init_db()`.

## Testing Instructions

### Backend Server
Backend is running on `http://10.46.0.83:8000` with the updated code. You should see:
- ✅ Database tables initialized successfully
- ✅ Critical ward model loaded successfully  
- ✅ General ward model loaded successfully

### Critical Ward Mode Testing
1. **Admit a CRITICAL patient** from the web dashboard (e.g., Myocardial Infarction patient)
2. **Open Android app** on your phone
3. **Click RED button** (Critical Ward button)
4. **Expected Results:**
   - Status should show "● Connected"
   - Active Alerts count should update
   - You should receive vital updates every 8 seconds
   - When ML predicts abnormal vitals (prediction = 1), phone should:
     - Vibrate with critical pattern
     - Show notification
     - Display alarm in Active Alerts list

### General Ward Mode Testing
1. **Admit a GENERAL patient** from the web dashboard (e.g., Pneumonia patient)
2. **Open Android app** on your phone
3. **Click GREEN button** (General Ward button)
4. **Expected Results:**
   - Status should show "● Registered"
   - Session ID should be displayed
   - Toggle "Simulate BLE Band" switch ON
   - Click "START SCANNING" button
   - Nearby Devices should show "BAND_01"
   - Proximity updates sent every 5 seconds
   - When nurse is nearby AND vitals abnormal, phone should:
     - Vibrate with general pattern
     - Show notification
     - Display alarm in Alerts for Nearby Patients list

## Known Issues & Workarounds

### Database Connection Pool Errors
**Symptom:** You may see `MaxClientsInSessionMode: max clients reached` errors in backend logs.

**Cause:** Supabase session mode limits the number of concurrent database connections.

**Impact:** 
- ❌ Nurse registration may fail with 500 Internal Server Error
- ❌ Some database operations may timeout

**Workaround Options:**
1. **Increase pool size** (temporary fix, may still hit Supabase limits):
   ```python
   # In backend/database.py line 29
   pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=20)
   ```

2. **Use connection pooling mode** instead of session mode in Supabase connection string:
   - Change from `:6543` (session pooler) to `:5432` (transaction pooler)
   - Update DATABASE_URL in environment

3. **Implement connection retry logic** in nurse registration endpoint

### Current Server Status
- ✅ Backend running with nurse broadcast fixes
- ✅ WebSocket endpoints operational (`/ws` and `/ws/nurse/{session_id}`)
- ⚠️ Database pool exhaustion causing intermittent failures
- ⚠️ Nurse registration returning 500 errors due to pool exhaustion

## Next Steps

1. **Test Android App:**
   - Test Critical Ward mode with critical patient
   - Test General Ward mode with general patient
   - Verify vibrations, notifications, and UI updates

2. **Fix Database Connection Issues:**
   - Increase pool size or switch to transaction pooler
   - Add retry logic to nurse registration
   - Implement proper connection management

3. **Polish Android UI:**
   - Add loading states
   - Improve error messages
   - Better alarm list formatting
   - Add patient details in alerts

4. **Prepare for Hardware Integration:**
   - Replace BLE simulation with real BLE scanning code
   - Test with actual BLE beacons/bands
   - Implement proper device filtering by MAC address

## Files Modified

- `backend/main.py` (lines 119-200): Added nurse broadcast loops and patient_type field
- `backend/database.py`: nurse_sessions table already existed

## Testing Commands

```bash
# Start backend server
cd backend
python main.py

# Start frontend (separate terminal)
cd frontend_new
npm run dev

# Check backend is accessible from phone
curl http://10.46.0.83:8000/

# Check WebSocket endpoint
curl http://10.46.0.83:8000/ws
```

## Success Criteria

✅ Critical Ward phone receives vital updates every 8 seconds
✅ Critical Ward phone vibrates when alarm triggered
✅ Critical Ward phone shows notifications
✅ General Ward phone can register successfully
✅ General Ward phone can simulate BLE scanning
✅ General Ward phone sends proximity updates
✅ General Ward phone receives alarms when nearby AND abnormal vitals
