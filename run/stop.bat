@echo off
REM ============================================================
REM  stop.bat - Stop LINE Archive Bot locally (Windows)
REM  Usage:    stop.bat
REM  Effect:   Kills all Python processes running app.py
REM ============================================================
setlocal enabledelayedexpansion
title LINE Archive Bot - Stopping...
set "SCRIPT_DIR=%~dp0"
echo [INFO] Looking for running LINE Archive Bot processes...
for /f "tokens=2 delims=," %%A in (
    'wmic process where "name='python.exe' and commandline like '%%app.py%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"'
) do (
    echo [INFO] Stopping PID: %%A
    taskkill /f /pid %%A >nul 2>&1
)
for /f "tokens=2 delims=," %%A in (
    'wmic process where "name='python.exe' and commandline like '%%waitress%%'" get processid /format:csv 2^>nul ^| findstr /r "[0-9]"'
) do (
    echo [INFO] Stopping waitress PID: %%A
    taskkill /f /pid %%A >nul 2>&1
)
echo [OK] All LINE Archive Bot processes stopped.
echo ============================================================
endlocal
