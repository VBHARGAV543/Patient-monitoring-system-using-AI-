@echo off
echo ===================================================
echo   Starting Backend Server Only
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

echo Checking backend directory...
cd /d "%~dp0backend"
if not exist "main.py" (
    echo ERROR: Backend files not found!
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Starting Backend Server...
echo ===================================================
echo.
echo Backend will be accessible at:
echo   - Local:   http://localhost:8000
echo   - Network: http://10.138.1.240:8000
echo.
echo Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Check if virtual environment exists
if exist "%~dp0.venv\Scripts\python.exe" (
    echo Using virtual environment...
    "%~dp0.venv\Scripts\python.exe" main.py
) else (
    echo Using system Python...
    python main.py
)

pause
