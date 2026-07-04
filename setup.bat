@echo off
REM ============================================================
REM  setup.bat - Zero-presets one-click deployment
REM  Usage:    Double-click setup.bat on a brand-new computer
REM  Effect:   Installs Python, Git, venv, deps, runs tests,
REM            configures .env, pushes to GitHub, deploys Render
REM ============================================================
setlocal enabledelayedexpansion
title LINE Archive Bot - One-Click Setup
color 0A

set "SCRIPT_DIR=%~dp0"
set "RUN_DIR=%SCRIPT_DIR%run"
set "VENV_DIR=%RUN_DIR%\venv"
set "REPORT_DIR=%SCRIPT_DIR%reports"

if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

echo ============================================================
echo  LINE Archive Bot - Zero-Presets One-Click Deployment
echo ============================================================
echo.

REM ---- Step 1: Check Python ----
echo [Step 1/7] Checking Python...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python not found!
    echo         Please install Python 3.9+ from https://www.python.org
    echo         Make sure "Add Python to PATH" is checked during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set "PY_VER=%%V"
echo [OK] Python %PY_VER% found.
echo.

REM ---- Step 2: Check Git ----
echo [Step 2/7] Checking Git...
git --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Git not found!
    echo         Please install Git from https://git-scm.com
    pause
    exit /b 1
)
for /f "tokens=3 delims= " %%V in ('git --version') do set "GIT_VER=%%V"
echo [OK] Git %GIT_VER% found.
echo.

REM ---- Step 3: Create virtual environment ----
echo [Step 3/7] Setting up virtual environment...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Creating venv...
    python -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)
echo.

REM ---- Step 4: Install dependencies ----
echo [Step 4/7] Installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip -q 2>nul
pip install -r "%RUN_DIR%\requirements.txt" -q
if !errorlevel! neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

REM ---- Step 5: Create .env if missing ----
echo [Step 5/7] Checking configuration...
if not exist "%RUN_DIR%\.env" (
    echo [INFO] .env not found. Creating from .env.example...
    copy "%RUN_DIR%\.env.example" "%RUN_DIR%\.env" >nul
    echo [WARN] .env created with defaults.
    echo        Please edit run\.env with your real credentials.
    echo.
    echo        Required keys:
    echo          LINE_CHANNEL_SECRET
    echo          LINE_CHANNEL_ACCESS_TOKEN
    echo          GMAIL_APP_PASSWORD
    echo          GITHUB_TOKEN
    echo          GROQ_API_KEY
    echo.
    echo        Press any key after editing .env to continue...
    pause >nul
) else (
    echo [OK] .env exists.
)
echo.

REM ---- Step 6: Run tests ----
echo [Step 6/7] Running automated tests...
cd /d "%RUN_DIR%"
python test_all.py
if !errorlevel! neq 0 (
    echo [WARN] Some tests failed. Check test_report.html for details.
) else (
    echo [OK] All tests passed.
)
echo.

REM ---- Step 7: Git init + push ----
echo [Step 7/7] Git setup and push...
cd /d "%SCRIPT_DIR%"
git rev-parse --git-dir >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] Initializing git repository...
    git init
)
git add -A
git status --porcelain | findstr /r "." >nul 2>&1
if !errorlevel! equ 0 (
    git commit -m "Auto-deploy: LINE Archive Bot setup"
    echo [OK] Changes committed.
) else (
    echo [OK] No changes to commit.
)

REM Check if remote exists
git remote get-url origin >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARN] No git remote configured.
    echo        Run: git remote add origin ^<your-repo-url^>
    echo        Then: git push -u origin main
) else (
    echo [INFO] Pushing to GitHub...
    git push -u origin main 2>nul
    if !errorlevel! neq 0 (
        echo [WARN] Push failed. Try manually: git push -u origin main
    ) else (
        echo [OK] Pushed to GitHub.
    )
)
echo.

REM ---- Generate report ----
echo ============================================================
echo  Setup Complete!
echo ============================================================
echo.
echo  Next steps:
echo    1. Edit run\.env with your credentials
echo    2. Run start.bat to start the bot locally
echo    3. Run stop.bat to stop the bot
echo    4. Run deploy.py to deploy to Render
echo.
echo  Reports:
echo    Test report:  run\test_report.html
echo    Deploy report: run\deploy_report.html
echo ============================================================
pause
endlocal
