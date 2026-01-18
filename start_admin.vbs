Set WshShell = CreateObject("WScript.Shell")

' Start Python assistant in visible console
WshShell.Run "cmd /c cd /d E:\ai_desktop_assistant && call venv\Scripts\activate && set PYTHONPATH=E:\ai_desktop_assistant && python -u core\main_controller.py", 1, False

' Start AutoHotkey for restart/quit hotkeys
WshShell.Run """C:\Program Files\AutoHotkey\AutoHotkey.exe"" ""E:\ai_desktop_assistant\tools\vt_overlay.ahk""", 0, False
