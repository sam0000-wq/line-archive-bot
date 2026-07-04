@echo off
REM ============================================================
REM  start.bat - Start LINE Archive Bot locally
REM  Usage:    start.bat
REM  Effect:   Activates venv, installs deps, starts Flask
REM ============================================================
setlocal enabledelayedexpansion
title LINE Archive Bot - Running
color 0B

set "SCRIPT_DIR=%~dp0"
set "RUN_DIR=%SCRIPT_DIR%run"
set "VENV_DIR=%RUN_DIR%\venv"

echo ============================================================
echo  LINE Archive Bot - Starting...
echo ============================================================
echo.

REM Auto-setup if venv missing
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] First run detected. Running setup...
    call "%SCRIPT_DIR%setup.bat"
    if !errorlevel! neq 0 (
        echo [ERROR] Setup failed.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"
cd /d "%RUN_DIR%"

echo [INFO] Starting on http://localhost:5000
echo [INFO] Health check: http://localhost:5000/health
echo [INFO] Press Ctrl+C to stop
echo ============================================================
python app.py
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application exited with code !errorlevel!.
    pause
)
endlocal
