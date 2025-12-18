@echo off
echo Starting Hospital Alarm Monitoring System...
echo.

echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "cd /d "c:\Users\Lenovo\Desktop\Alarm fatigue #prototype\backend" && python main.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
cd /d "c:\Users\Lenovo\Desktop\Alarm fatigue #prototype\frontend_new"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop the frontend server
echo Close the Backend Server window to stop the backend
echo.

call npm run dev

pause
