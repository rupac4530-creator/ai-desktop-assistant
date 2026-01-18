@echo off
REM ================================================
REM AUTOPILOT KILL-SWITCH
REM Disables all automatic repairs and updates
REM ================================================

echo.
echo ========================================
echo   DISABLING AUTOPILOT
echo ========================================
echo.

cd /d "%~dp0.."

powershell -Command "(Get-Content .env) -replace 'SELF_UPDATE_AUTO_APPLY=true','SELF_UPDATE_AUTO_APPLY=false' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace 'SELF_HEAL_AUTO_REPAIR=true','SELF_HEAL_AUTO_REPAIR=false' | Set-Content .env"

echo [OK] SELF_UPDATE_AUTO_APPLY=false
echo [OK] SELF_HEAL_AUTO_REPAIR=false
echo.

taskkill /IM python.exe /F 2>nul

echo Autopilot DISABLED.
pause
