@echo off
REM ============================================================
REM  stop.bat - Stop LINE Archive Bot locally
REM  Usage:    stop.bat
REM  Effect:   Kills all Python processes running app.py
REM ============================================================
setlocal enabledelayedexpansion
title LINE Archive Bot - Stopped
color 0C

echo ============================================================
echo  LINE Archive Bot - Stopping...
echo ============================================================
echo.

echo [INFO] Looking for running processes...
set "FOUND=0"

for /f "tokens=2 delims=," %%A in (
    'wmic process where "name='python.exe' and commandline like '%%app.py%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"'
) do (
    echo [INFO] Stopping PID: %%A
    taskkill /f /pid %%A >nul 2>&1
    set "FOUND=1"
)

for /f "tokens=2 delims=," %%A in (
    'wmic process where "name='python.exe' and commandline like '%%gunicorn%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"'
) do (
    echo [INFO] Stopping gunicorn PID: %%A
    taskkill /f /pid %%A >nul 2>&1
    set "FOUND=1"
)

if "!FOUND!"=="0" (
    echo [INFO] No running processes found.
) else (
    echo [OK] All processes stopped.
)
echo ============================================================
pause
endlocal
