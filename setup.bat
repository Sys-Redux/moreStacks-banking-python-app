@echo off
REM moreStacks Banking Setup Script for Windows
REM Automatically installs dependencies and launches the application

echo ============================================================
echo   moreStacks Banking - Setup Script
echo   Banking Made Simple
echo ============================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from python.org
    pause
    exit /b 1
)

echo Installing dependencies...
echo This may take a minute...
echo.

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    echo Please try manually: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Launching moreStacks Banking...
echo ============================================================
echo.

python main.py

pause
