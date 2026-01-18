@echo off
title AI Desktop Assistant
cd /d E:\ai_desktop_assistant\tools

echo Starting hotkey overlay...
start "" "C:\Program Files\AutoHotkey\AutoHotkey.exe" "vt_overlay.ahk"

cd /d E:\ai_desktop_assistant
echo Starting AI assistant...
call venv\Scripts\activate.bat
start "" python core\main_controller.py

echo.
echo ============================================
echo HOTKEYS ACTIVE:
echo   Ctrl+Alt+H     = Show/Hide VTube Studio
echo   Ctrl+Alt+A     = Toggle Overlay
echo   Ctrl+Alt+Space = Push-to-talk (hold)
echo   Ctrl+Alt+T     = Type command
echo ============================================
timeout /t 5
