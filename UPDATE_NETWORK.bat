@echo off
setlocal EnableDelayedExpansion

REM ===================================================================
REM  NETWORK UPDATE SCRIPT - Patient Monitoring System
REM  Updates configuration when network/IP changes
REM ===================================================================

color 0E
title Patient Monitoring System - Network Update

echo.
echo ====================================================================
echo   PATIENT MONITORING SYSTEM - NETWORK UPDATE
echo ====================================================================
echo.

REM ===================================================================
REM  STEP 1: Detect Current IP Address
REM ===================================================================

echo [1/3] Detecting new network configuration...
echo.

REM Use PowerShell to detect the current IP
for /f "tokens=*" %%i in ('powershell -Command "Try { $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1).IPAddress; if ($ip) { Write-Output $ip } else { Write-Output 'localhost' } } Catch { Write-Output 'localhost' }"') do set NEW_IP=%%i

echo    New IP Address: %NEW_IP%
echo.

REM Check if .env exists to show old IP
set FRONTEND_DIR=%~dp0frontend_new
set ENV_FILE=%FRONTEND_DIR%\.env

if exist "%ENV_FILE%" (
    echo    Previous configuration will be updated
) else (
    echo    No previous configuration found - creating new one
)

echo.

REM ===================================================================
REM  STEP 2: Update Frontend .env File
REM ===================================================================

echo [2/3] Updating frontend configuration...
echo.

if not exist "%FRONTEND_DIR%" (
    echo    ERROR: Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

REM Create/update .env file with new IP
(
    echo # Backend API Configuration
    echo # Auto-updated by UPDATE_NETWORK.bat on %date% at %time%
    echo # Current IP: %NEW_IP%
    echo.
    echo VITE_API_URL=http://%NEW_IP%:8000
    echo VITE_WS_URL=ws://%NEW_IP%:8000
) > "%ENV_FILE%"

echo    ✓ Updated: frontend_new\.env
echo    ✓ New API URL: http://%NEW_IP%:8000
echo.

REM ===================================================================
REM  STEP 3: Display QR Code Instructions
REM ===================================================================

echo [3/3] Mobile app configuration...
echo.

echo    Mobile App Update Required:
echo    -----------------------------------------------------------------
echo    Option 1: Scan QR Code (Recommended)
echo       1. Start backend server (START_BACKEND.bat or START_ALL.bat)
echo       2. QR code will appear in the backend window
echo       3. Open Nurse Alarm App → Settings → Network Settings
echo       4. Tap "Scan QR Code"
echo       5. Scan the QR code from backend window
echo.
echo    Option 2: Manual Entry
echo       1. Open Nurse Alarm App
echo       2. Go to Settings → Network Settings
echo       3. Enter: http://%NEW_IP%:8000
echo       4. Tap "Test Connection"
echo       5. Tap "Save"
echo    -----------------------------------------------------------------
echo.

REM ===================================================================
REM  SUMMARY
REM ===================================================================

echo ====================================================================
echo   CONFIGURATION UPDATED SUCCESSFULLY!
echo ====================================================================
echo.
echo   New Network Settings:
echo      IP Address:  %NEW_IP%
echo      Backend:     http://%NEW_IP%:8000
echo      WebSocket:   ws://%NEW_IP%:8000
echo      API Docs:    http://%NEW_IP%:8000/docs
echo.
echo   Frontend configuration updated in: frontend_new\.env
echo.
echo   Next Steps:
echo      1. Restart servers if they are running (recommended)
echo      2. Update mobile app using one of the options above
echo      3. Test connection from all devices
echo.
echo ====================================================================
echo.

REM Ask if user wants to restart servers
echo Would you like to restart the servers now? (Y/N)
set /p RESTART="> "

if /i "%RESTART%"=="Y" (
    echo.
    echo    Restarting servers...
    echo.
    
    REM Kill existing Python and Node processes (if any)
    echo    Stopping running servers...
    taskkill /F /IM python.exe /T >nul 2>&1
    taskkill /F /IM node.exe /T >nul 2>&1
    timeout /t 2 /nobreak >nul
    
    REM Start servers
    echo    Starting backend and frontend...
    cd /d "%~dp0"
    call START_ALL.bat
    
) else (
    echo.
    echo    Reminder: You'll need to restart the servers manually
    echo    for the new network configuration to take effect.
    echo.
    echo    Run START_ALL.bat to restart both servers.
    echo.
    pause
)

exit /b 0
