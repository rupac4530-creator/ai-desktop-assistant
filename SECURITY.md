# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability in AI Desktop Assistant, please report it responsibly.

### 📧 How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, email the maintainer directly:

**Email:** rupac4530@gmail.com  
**Subject:** [SECURITY] AI Desktop Assistant - Brief description

### 📝 What to Include

1. **Description** of the vulnerability
2. **Steps to reproduce**
3. **Potential impact**
4. **Suggested fix** (if any)
5. **Your contact information** (for follow-up)

### ⏱️ Response Timeline

| Stage | Timeframe |
|-------|-----------|
| Acknowledgment | 48 hours |
| Initial assessment | 7 days |
| Fix development | 14-30 days |
| Public disclosure | After fix released |

### 🏆 Recognition

We appreciate security researchers who report vulnerabilities responsibly.

- Your name will be added to our Security Hall of Fame (with permission)
- We will credit you in the security advisory
- No bug bounty program at this time (open-source project)

## Security Considerations

### ⚠️ Important Notes

This application has **full system access** by design. It can:

- Execute shell commands
- Read/write files
- Control mouse/keyboard
- Access network

### 🛡️ Built-in Protections

1. **Kill Switch** (`Ctrl+Alt+K`) — Emergency stop
2. **Circuit Breaker** — Limits auto-repair attempts
3. **Git Rollback** — All changes reversible
4. **Approval Mode** — Optional confirmation for actions
5. **Offline-First** — No data sent to external servers

### 🔐 Recommended Practices

1. **Don't run as Administrator** unless required
2. **Review `.env` file** — Contains configuration
3. **Check logs regularly** — `logs/` directory
4. **Keep software updated** — Pull latest from main branch
5. **Use a dedicated user account** if concerned

### 📋 Audit Log

All actions are logged to:
- `logs/last_session_debug.log` — Current session
- `logs/self_heal.log` — Repair actions
- `logs/stt_transcripts.log` — Voice commands

### 🚫 Known Limitations

- No sandboxing of executed commands
- No permission system for tools
- Avatar connection not encrypted (local only)
- LLM responses are not validated before execution (in auto mode)

---

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.2) and announced via:

- GitHub Releases
- README.md updates
- Security advisories (for critical issues)

---

*Thank you for helping keep AI Desktop Assistant secure!*
