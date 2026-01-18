@echo off
REM ================================================
REM ENABLE AUTOPILOT
REM Re-enables automatic repairs and updates
REM ================================================

echo.
echo ========================================
echo   ENABLING AUTOPILOT
echo ========================================
echo.

cd /d "%~dp0.."

powershell -Command "(Get-Content .env) -replace 'SELF_UPDATE_AUTO_APPLY=false','SELF_UPDATE_AUTO_APPLY=true' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace 'SELF_HEAL_AUTO_REPAIR=false','SELF_HEAL_AUTO_REPAIR=true' | Set-Content .env"

echo [OK] SELF_UPDATE_AUTO_APPLY=true
echo [OK] SELF_HEAL_AUTO_REPAIR=true
echo.

echo Autopilot ENABLED.
echo Starting assistant...
start "" venv\Scripts\python.exe core\main_controller.py

pause
