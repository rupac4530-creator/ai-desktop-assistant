@echo off
cd /d E:\ai_desktop_assistant\tools
start "" "C:\Program Files\AutoHotkey\AutoHotkey.exe" "vt_overlay.ahk"
cd /d E:\ai_desktop_assistant
call venv\Scripts\activate.bat
start "" python core\main_controller.py