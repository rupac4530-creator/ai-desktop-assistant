#SingleInstance Force
#Persistent
SetTitleMatchMode, 2

; Track visibility state
global vtube_visible := false
global assistant_started := false

; Ctrl+Alt+H - Toggle VTube Studio visibility and manage assistant
^!h::
    ; Check if Python assistant is running
    Process, Exist, python.exe
    pythonPid := ErrorLevel
    
    if (pythonPid = 0) {
        ; Python not running - restart it
        MsgBox, 4, AI Assistant, Assistant not running. Start it now?
        IfMsgBox, Yes
        {
            Run, wscript.exe "E:\ai_desktop_assistant\start_admin.vbs",, Hide
            Sleep, 3000
            TrayTip, AI Assistant, Assistant started!, 2
        }
        return
    }
    
    ; Try to toggle VTube Studio
    IfWinExist, VTube Studio
    {
        if (vtube_visible) {
            WinHide, VTube Studio
            vtube_visible := false
            TrayTip, AI Assistant, Avatar hidden, 1
        } else {
            WinShow, VTube Studio
            WinActivate, VTube Studio
            vtube_visible := true
            TrayTip, AI Assistant, Avatar shown, 1
        }
    }
    else
    {
        ; VTube Studio not running - offer to start it
        TrayTip, AI Assistant, VTube Studio not running, 2
    }
return

; Ctrl+Alt+Q - Quit assistant
^!q::
    MsgBox, 4, AI Assistant, Stop the assistant?
    IfMsgBox, Yes
    {
        Process, Close, python.exe
        TrayTip, AI Assistant, Assistant stopped, 2
    }
return

; Ctrl+Alt+R - Restart assistant
^!r::
    TrayTip, AI Assistant, Restarting..., 1
    Process, Close, python.exe
    Sleep, 1000
    Run, wscript.exe "E:\ai_desktop_assistant\start_admin.vbs",, Hide
    Sleep, 3000
    TrayTip, AI Assistant, Restarted!, 2
return