# Desktop Overlay + Hotkey-Controlled Assistant Setup

This setup provides a **desktop overlay avatar** that is always visible on your desktop with **transparent background** and **click-through capability**, controlled entirely by **hotkeys** and **voice commands**.

## 🎯 What This Setup Gives You

| Feature                  | Status             |
| ------------------------ | ------------------ |
| Avatar on desktop        | ✅ YES              |
| Transparent              | ✅ YES              |
| Apps visible behind      | ✅ YES              |
| Click-through            | ✅ YES (Ctrl+Alt+A) |
| Always on top            | ✅ YES              |
| Show / Hide instantly    | ✅ YES (Ctrl+Alt+H) |
| Voice commands           | ✅ YES              |
| Keyboard commands        | ✅ YES              |
| No fullscreen            | ✅ YES              |
| No OBS                   | ✅ YES              |

## 🚀 Quick Start

### Step 1: Start Everything
```cmd
Double-click: E:\ai_desktop_assistant\run_assistant_with_overlay.bat
```

This batch file:
- Starts your AI assistant (Python)
- Starts the overlay controller (AutoHotkey)
- Waits for VTube Studio to be ready

### Step 2: Start VTube Studio
- Launch VTube Studio manually
- Enable Desktop Overlay mode in VTube Studio settings
- Position your avatar where you want it

### Step 3: Control with Hotkeys

| Action                                         | Hotkey             |
| ---------------------------------------------- | ------------------ |
| Toggle click-through + always-on-top           | **Ctrl + Alt + A** |
| Show / Hide avatar instantly                   | **Ctrl + Alt + H** |

## 🎤 Voice Commands

Once running, you can say things like:

- **"Open YouTube"** → Opens YouTube behind the avatar
- **"Search Biology 2024 questions"** → Opens browser + searches
- **"Open ChatGPT"** → Opens ChatGPT
- **"Copy this and paste in VS Code"** → Copies and pastes
- **"Hide yourself"** → Avatar disappears (Ctrl+Alt+H)
- **"Come back"** → Avatar reappears (Ctrl+Alt+H)
- **"Take screenshot"** → Takes a screenshot
- **"Volume up/down/mute"** → Adjusts system volume

## 🔧 Technical Details

### Files Used
- `run_assistant_with_overlay.bat` - Main launcher
- `tools/vt_overlay.ahk` - AutoHotkey overlay controller
- `core/main_controller.py` - AI assistant brain

### AutoHotkey Script Features
- **Ctrl+Alt+A**: Toggles click-through and always-on-top
- **Ctrl+Alt+H**: Shows/hides VTube Studio window
- Automatically finds VTube Studio window by title or process name
- Provides visual feedback with tooltips

### Safety Features
- Dangerous actions require confirmation
- Allowlist system for permitted commands
- Confirmation system for shutdown/restart operations

## 🛑 Important Notes

- **Do NOT** use VTube Studio fullscreen mode
- **Do NOT** rely on clicking VTube Studio UI buttons
- Control is now **hotkey + AI voice**, not manual UI clicking
- AutoHotkey must be installed (already done in this setup)

## 🔧 Troubleshooting

### Avatar not responding to hotkeys?
- Make sure VTube Studio is running
- Check if AutoHotkey script is running in system tray
- Try restarting the batch file

### Voice commands not working?
- Check microphone permissions
- Ensure Python virtual environment is activated
- Check console output for errors

### Overlay not transparent?
- Press **Ctrl+Alt+A** to enable click-through mode
- In VTube Studio, ensure "Desktop Overlay" is enabled

## 📁 Project Structure
```
ai_desktop_assistant/
├── run_assistant_with_overlay.bat    # Main launcher
├── tools/
│   └── vt_overlay.ahk               # Hotkey controller
├── core/
│   └── main_controller.py           # AI assistant
├── config/
│   ├── allowlist.txt                # Permitted commands
│   └── dangerous_actions.txt        # Actions needing confirmation
└── speech/
    ├── speech_to_text.py
    └── text_to_speech.py
```

## 🎉 You're Done!

This is the **professional, stable setup** you wanted. The avatar stays visible, transparent, and interactive without blocking your workflow. Control it with hotkeys and voice - no more manual UI hunting!