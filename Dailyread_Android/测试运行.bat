@echo off
cd /d "%~dp0"
echo Testing environment...
echo.

echo 1. Current directory:
cd
echo.

echo 2. Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
)
echo.

echo 3. Checking dailyread_manager.py...
if exist dailyread_manager.py (
    echo OK: dailyread_manager.py exists
) else (
    echo ERROR: dailyread_manager.py not found
)
echo.

echo 4. Testing import...
python -c "import sys; print('Python OK')"
echo.

echo 5. Trying to run (will exit immediately)...
python dailyread_manager.py

echo.
echo Script completed. Press any key...
pause >nul

