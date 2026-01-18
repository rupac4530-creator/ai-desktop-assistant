@echo off
title AI Desktop Assistant
cd /d E:\ai_desktop_assistant
call venv\Scripts\activate.bat

echo ============================================
echo    AI Desktop Assistant
echo    Starting with system tray...
echo ============================================
echo.

python core\main_controller.py --tray

pause
