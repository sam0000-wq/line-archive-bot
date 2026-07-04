@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

set RENDER_API_KEY=rnd_ohtuqV5qS7KdPFw5YA28Ci9PzEvG
set RENDER_SERVICE_ID=srv-d92hf8faqgkc739e03qg

title LINE Archive Bot - Deploy
color 0B

echo ============================================
echo   LINE Archive Bot - Deploy
echo   %date% %time%
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Running tests...
cd run
call python test_all.py
if %errorlevel% neq 0 (
    echo.
    echo [FAIL] Tests failed. Deploy aborted.
    echo.
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] Git add + commit...
git add -A
git status --short
echo.

echo [3/4] Git push...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo [FAIL] Push failed.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Triggering Render deploy...
cd run
call python deploy.py --auto
cd ..

echo.
echo ============================================
echo   Deploy complete!
echo ============================================
echo.
pause
