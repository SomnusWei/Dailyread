@echo off
chcp 65001 >nul
title yixue-zonghe Platform
setlocal

set "HERE=%~dp0"

echo ============================================================
echo   yixue-zonghe  Personal Workbench
echo ============================================================
echo.

set "PYTHON="
if defined YIXUE_PYTHON if exist "%YIXUE_PYTHON%" set "PYTHON=%YIXUE_PYTHON%"
if not defined PYTHON if exist "C:\Users\somnu\.workbuddy\binaries\python\envs\default\Scripts\python.exe" set "PYTHON=C:\Users\somnu\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not defined PYTHON for %%I in (python.exe) do if not defined PYTHON set "PYTHON=%%~$PATH:I"

if not defined PYTHON goto nopython
if not exist "%HERE%start.py" goto noscript

echo   Python : %PYTHON%
echo   Script : %HERE%start.py
echo   URL    : http://127.0.0.1:8770/   (default, override with --port N)
echo ============================================================
echo   The browser opens automatically. Close this window to stop.
echo.

"%PYTHON%" "%HERE%start.py" %*
echo.
echo [Server exited]
goto end

:noscript
echo [ERROR] start.py not found next to this script:
echo         %HERE%start.py
goto end

:nopython
echo [ERROR] Python interpreter not found.
echo.
echo   Fix by either:
echo     1) Installing Python and adding it to PATH, or
echo     2) Setting the YIXUE_PYTHON environment variable, e.g.
echo        set YIXUE_PYTHON=C:\Path\to\python.exe
goto end

:end
echo.
pause
