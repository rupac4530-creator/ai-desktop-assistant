#SingleInstance force
#Persistent
SetTitleMatchMode, 2
DetectHiddenWindows, On

Menu, Tray, Tip, AI Assistant Hotkeys Active
Menu, Tray, Add, Test Hotkey (Ctrl+Alt+H), TestHotkey
Menu, Tray, Add, Exit, ExitApp

; SIMPLE TEST - Ctrl+Alt+H shows a message
^!h::
    MsgBox, 64, Hotkey Working!, Ctrl+Alt+H was pressed!`n`nThis proves hotkeys are working.`nNow we need to connect it to your assistant.
    return

; Ctrl+Alt+A - another test
^!a::
    MsgBox, 64, Hotkey Working!, Ctrl+Alt+A was pressed!
    return

; Ctrl+Alt+Space - PTT test
^!Space::
    MsgBox, 64, Hotkey Working!, Ctrl+Alt+Space was pressed!
    return

; Ctrl+Alt+T - Toggle test
^!t::
    MsgBox, 64, Hotkey Working!, Ctrl+Alt+T was pressed!
    return

TestHotkey:
    MsgBox, 64, Test, Hotkeys are registered. Press Ctrl+Alt+H to test.
    return

ExitApp:
    ExitApp
    return
