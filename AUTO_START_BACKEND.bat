@echo off
echo ========================================
echo   AUTO-STARTING BACKEND SERVER
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if virtual environment exists
if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run the main setup first.
    pause
    exit /b 1
)

REM Change to backend directory
cd /d "%SCRIPT_DIR%backend"

echo Starting Python backend server...
echo Camera will be available at: http://10.138.1.240:8000/stream
echo.
echo Keep this window open while using the app!
echo.

REM Start the backend server
"%SCRIPT_DIR%.venv\Scripts\python.exe" main.py

pause
