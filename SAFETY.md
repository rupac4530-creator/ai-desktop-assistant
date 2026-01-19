# Safety Documentation

This document explains the safety features, kill switches, and how to disable autonomous operations.

---

## ⚠️ Important Safety Information

The AI Desktop Assistant can control your computer autonomously. While extensive safeguards are in place, you should understand how to stop it immediately if needed.

---

## 🛑 Emergency Kill Switch

### Immediate Stop: `Ctrl+Alt+K`

Press this hotkey combination to **immediately halt all operations**:
- Stops any running automation
- Cancels pending voice commands
- Pauses the autonomous brain
- Disables self-healing temporarily

### Manual Kill Script

If hotkeys are unresponsive, run:

```powershell
# Navigate to project
cd E:\ai_desktop_assistant

# Run kill script
.\tools\disable_autopilot.bat
```

Or in PowerShell:
```powershell
# Force stop all Python processes related to assistant
Get-Process python* | Where-Object { $_.Path -like "*ai_desktop_assistant*" } | Stop-Process -Force
```

---

## 🔒 Safety Features

### 1. Confirmation Required Actions

The following actions require explicit user confirmation:
- Deleting files or folders
- Modifying system settings
- Installing software
- Sending emails or messages
- Financial transactions
- Any action flagged as "high-risk"

### 2. Sandboxed Operations

- File operations are limited to user directories by default
- System directories are protected
- Registry modifications are blocked
- Network access is logged

### 3. Rate Limiting

- Maximum 3 autonomous repairs per 10 minutes
- Maximum 500 lines of code changes per commit
- Automatic pause after repeated failures

### 4. Audit Logging

Every action is logged to:
- `logs/autonomous_patch_log.jsonl` - Code changes
- `logs/git_actions.jsonl` - Git operations
- `logs/self_heal_report.jsonl` - Repair attempts
- `logs/stt_transcripts.log` - Voice commands

### 5. Git-Backed Rollback

All code changes are committed to Git with:
- Automatic branch creation before changes
- Instant rollback capability
- Full history preserved

---

## ⚙️ Disabling Autonomous Features

### Disable Self-Healing

Edit `.env` and set:
```ini
SELF_HEAL_AUTO_REPAIR=false
SELF_HEAL_ENABLED=false
```

### Disable Full Autonomy

Edit `.env` and set:
```ini
FULL_AUTONOMY=false
```

### Disable Autonomous Coding

Edit `.env` and set:
```ini
AUTONOMOUS_CODER_ENABLED=false
```

### Disable Self-Update

Edit `.env` and set:
```ini
SELF_UPDATE_ENABLED=false
```

---

## 🔧 Safe Mode

To run in safe mode (no autonomous actions):

```powershell
# Set environment variable before starting
$env:SAFE_MODE = "true"
python core/main_controller.py
```

Or create a `safe_start.bat`:
```batch
@echo off
set SAFE_MODE=true
set FULL_AUTONOMY=false
set SELF_HEAL_AUTO_REPAIR=false
cd /d E:\ai_desktop_assistant
call venv\Scripts\activate
python core\main_controller.py
```

---

## 📋 Safety Checklist

Before running the assistant:

- [ ] Review `.env` settings
- [ ] Understand the kill switch (`Ctrl+Alt+K`)
- [ ] Know where logs are stored (`logs/` directory)
- [ ] Back up important files if testing new features
- [ ] Test with `FULL_AUTONOMY=false` first

---

## 🚨 What To Do If Something Goes Wrong

1. **Press `Ctrl+Alt+K`** immediately
2. If unresponsive, run `tools\disable_autopilot.bat`
3. If still running, open Task Manager and end Python processes
4. Check logs in `logs/` directory for what happened
5. Use Git to rollback changes:
   ```powershell
   git log --oneline -10  # See recent changes
   git reset --hard HEAD~1  # Rollback last change
   ```

---

## 📞 Reporting Safety Issues

If you discover a safety vulnerability:

1. **Do not** post publicly
2. Email: [security@example.com]
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Potential impact

---

## ⚖️ Disclaimer

This software is provided "as-is" without warranty. The developers are not responsible for:
- Unintended actions performed by the assistant
- Data loss or corruption
- System instability
- Any damages arising from use

Always maintain backups and use at your own risk.
