@echo off
title AI Desktop Assistant with Overlay
cd /d E:\ai_desktop_assistant

echo ============================================
echo    AI Desktop Assistant + Avatar Overlay
echo ============================================
echo.

REM Activate virtualenv
call venv\Scripts\activate.bat

REM Start the overlay AHK script first
echo Starting overlay controller...
start "" "C:\Program Files\AutoHotkey\AutoHotkey.exe" "E:\ai_desktop_assistant\tools\vt_overlay.ahk"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start assistant
echo Starting AI assistant...
echo.
echo HOTKEYS:
echo   Ctrl+Alt+A = Toggle click-through + always-on-top
echo   Ctrl+Alt+H = Show/Hide avatar
echo.
echo Say "Open YouTube", "Search...", etc.
echo Press Ctrl+C to exit.
echo ============================================
echo.

python core\main_controller.py

pause
