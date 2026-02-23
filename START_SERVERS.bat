@echo off
echo ===================================================
echo   Hospital Alarm Monitoring System - Startup
echo ===================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if Node.js is available
call npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js/npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Checking Backend Dependencies...
cd /d "%~dp0backend"
if not exist "main.py" (
    echo ERROR: Backend files not found!
    pause
    exit /b 1
)
echo Backend found: OK

echo.
echo [2/3] Checking Frontend Dependencies...
cd /d "%~dp0frontend_new"
if not exist "package.json" (
    echo ERROR: Frontend files not found!
    pause
    exit /b 1
)

if not exist "node_modules\" (
    echo Installing frontend dependencies... This may take a few minutes.
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)
echo Frontend dependencies: OK

echo.
echo [3/3] Starting Servers...
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && echo Starting backend on http://localhost:8000 && python main.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
echo.
echo ===================================================
echo   Servers Starting!
echo ===================================================
echo.
echo Backend:  http://localhost:8000
echo          http://10.138.1.240:8000 (network)
echo.
echo Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop the frontend server
echo Close the Backend Server window to stop the backend
echo ===================================================
echo.

call npm run dev

pause
