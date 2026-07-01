@echo off
REM ============================================================
REM  start.bat - Start LINE Archive Bot locally (Windows)
REM  Usage:    start.bat
REM  Effect:   Activates venv, installs deps, starts Flask on :5000
REM ============================================================
setlocal enabledelayedexpansion
title LINE Archive Bot - Starting...
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Creating...
    cd /d "%SCRIPT_DIR%"
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo         Make sure Python 3.9+ is installed and on PATH.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)
call "%VENV_DIR%\Scripts\activate.bat"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [INFO] Virtual environment activated.
echo [INFO] Installing dependencies from requirements.txt...
python -m pip install --upgrade pip -q
pip install -r "%SCRIPT_DIR%requirements.txt" -q
if !errorlevel! neq 0 (
    echo [ERROR] pip install failed. Check requirements.txt.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
if not exist "%SCRIPT_DIR%.env" (
    echo [WARN] .env file not found. Copying from .env.example...
    copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
    echo [WARN] Please edit .env with your real credentials, then re-run start.bat.
    pause
    exit /b 1
)
echo [INFO] Starting LINE Archive Bot on http://localhost:5000
echo [INFO] Health check: http://localhost:5000/health
echo ============================================================
cd /d "%SCRIPT_DIR%"
python app.py
if !errorlevel! neq 0 (
    echo [ERROR] Application exited with code !errorlevel!.
    pause
    exit /b !errorlevel!
)
endlocal
