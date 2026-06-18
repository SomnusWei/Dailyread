@echo off
REM Force switch to script directory
cd /d "%~dp0"
title DailyRead Data Manager
color 0A

echo ========================================
echo     DailyRead Data Manager
echo ========================================
echo.

echo [INFO] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3.7+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found
echo.

echo [INFO] Checking dependencies...
python -c "import pandas, openpyxl, requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install pandas openpyxl requests
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        echo Please run manually: pip install pandas openpyxl requests
        echo.
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed
    echo.
)

echo [INFO] Starting application...
echo.

python dailyread_manager.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error
    pause
)

