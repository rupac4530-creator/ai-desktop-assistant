# Privacy Policy

This document explains what data the AI Desktop Assistant collects, stores, and how it's used.

---

## 🔒 Privacy Summary

**TL;DR**: This assistant runs 100% locally. Your data stays on your machine. No telemetry, no cloud uploads, no tracking.

---

## 📊 Data Collection

### What IS Collected (Locally Only)

| Data Type | Purpose | Storage Location | Retention |
|-----------|---------|------------------|-----------|
| Voice recordings | Transcription | Temporary files | Deleted after processing |
| Transcribed text | Command processing | `logs/stt_transcripts.log` | Until manually deleted |
| Command history | Context/debugging | `logs/` directory | Until manually deleted |
| Error logs | Debugging | `logs/` directory | Until manually deleted |
| Git history | Change tracking | `.git/` directory | Permanent (local) |

### What IS NOT Collected

- ❌ No data sent to external servers (unless you enable cloud APIs)
- ❌ No telemetry or analytics
- ❌ No user identification
- ❌ No browsing history beyond current session
- ❌ No keystroke logging beyond explicit commands
- ❌ No screenshots unless explicitly requested

---

## 🌐 External Services (Optional)

If you choose to enable external APIs, data may be sent to:

| Service | Data Sent | When Used |
|---------|-----------|-----------|
| OpenAI API | Text prompts | If `OPENAI_API_KEY` is set |
| Anthropic API | Text prompts | If `ANTHROPIC_API_KEY` is set |
| Ollama (local) | Text prompts | Local only - no external transfer |

**To disable all external APIs**: Remove or comment out API keys in `.env`

---

## 🎤 Voice Data

### How Voice is Processed

1. Audio is captured when you press the PTT hotkey
2. Audio is processed locally by Faster-Whisper
3. Transcribed text is used for commands
4. Original audio is deleted immediately after transcription

### Voice Data Storage

- **Temporary WAV files**: Created in `temp/`, deleted after processing
- **Transcripts**: Stored in `logs/stt_transcripts.log` (text only)
- **No permanent audio storage** by default

### Disabling Voice Logging

Edit `.env`:
```ini
LOG_TRANSCRIPTS=false
```

---

## 📁 Log Files

### What's in the Logs

| Log File | Contents |
|----------|----------|
| `logs/stt_transcripts.log` | Voice command transcripts |
| `logs/last_session_debug.log` | Debug information |
| `logs/self_heal_report.jsonl` | Repair action records |
| `logs/autonomous_patch_log.jsonl` | Code changes |
| `logs/git_actions.jsonl` | Git operations |

### Deleting Logs

```powershell
# Delete all logs
Remove-Item E:\ai_desktop_assistant\logs\* -Force

# Delete specific log types
Remove-Item E:\ai_desktop_assistant\logs\stt_*.log -Force
```

### Disabling Logging

Edit `.env`:
```ini
DEBUG_LOGGING=false
LOG_TRANSCRIPTS=false
LOG_COMMANDS=false
```

---

## 🔐 Sensitive Data Protection

### API Keys

- Stored only in `.env` (local file)
- Never logged or transmitted
- Never committed to Git (`.env` is in `.gitignore`)

### Passwords

- Never stored by the assistant
- Never logged
- If spoken, immediately discarded after processing

### Personal Files

- Only accessed when explicitly requested
- No indexing or scanning of personal files
- No upload of file contents

---

## 👤 User Identification

This software does **not**:
- Create user accounts
- Require registration
- Track user identity
- Collect personal information
- Use cookies or tracking pixels

---

## 🌍 Data Location

All data remains on your local machine:
- Project directory: `E:\ai_desktop_assistant\`
- Logs: `E:\ai_desktop_assistant\logs\`
- Models: `E:\ai_desktop_assistant\models\`
- Config: `E:\ai_desktop_assistant\.env`

No data is stored externally unless you explicitly configure cloud services.

---

## 🗑️ Data Deletion

### Complete Data Removal

```powershell
# Stop the assistant first
# Then remove everything:
Remove-Item -Recurse -Force E:\ai_desktop_assistant
```

### Selective Deletion

```powershell
# Delete logs only
Remove-Item -Recurse -Force E:\ai_desktop_assistant\logs\*

# Delete cached models
Remove-Item -Recurse -Force E:\ai_desktop_assistant\models\*

# Delete Git history
Remove-Item -Recurse -Force E:\ai_desktop_assistant\.git
```

---

## 📜 Third-Party Services

If enabled, these services have their own privacy policies:

- **OpenAI**: https://openai.com/privacy/
- **Anthropic**: https://www.anthropic.com/privacy
- **Ollama**: Runs locally, no external data transfer

---

## 🔄 Updates to This Policy

This privacy policy may be updated. Check `PRIVACY.md` in the repository for the latest version.

---

## 📞 Contact

For privacy concerns or questions:
- Email: [privacy@example.com]
- GitHub Issues: [repository link]

---

*Last updated: January 2026*
