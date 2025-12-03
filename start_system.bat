@echo off
REM Windows batch script to run the distributed system

echo ============================================================
echo   DISTRIBUTED SYSTEM SIMULATION - LAUNCHER
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Run pre-flight check
echo Running system verification...
echo.
python test_system.py
if errorlevel 1 (
    echo.
    echo ERROR: System verification failed
    echo Please fix the issues above before continuing
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   STARTING DISTRIBUTED SYSTEM
echo ============================================================
echo.
echo The system will start all nodes automatically.
echo Press Ctrl+C to stop the system at any time.
echo.
pause

REM Run the system
python run_system.py

echo.
echo ============================================================
echo   SYSTEM STOPPED
echo ============================================================
echo.
pause
