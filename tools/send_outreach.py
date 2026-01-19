#!/usr/bin/env python3
"""
Outreach Email Sender for AI Desktop Assistant
Author: Bedanta Chatterjee

Usage:
    python tools/send_outreach.py --prepare    # Generate emails without sending
    python tools/send_outreach.py --send       # Send emails (requires SMTP creds)
    python tools/send_outreach.py --dry-run    # Show what would be sent

Environment Variables Required for --send:
    OUTREACH_SMTP_HOST   (e.g., smtp.gmail.com)
    OUTREACH_SMTP_PORT   (e.g., 587)
    OUTREACH_SMTP_USER   (your email)
    OUTREACH_SMTP_PASS   (app password)
"""

import csv
import os
import sys
import argparse
import smtplib
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "assets" / "recruiters.csv"
TEMPLATE_PATH = BASE_DIR / "assets" / "recruiter_email_template.txt"
PREPARED_DIR = BASE_DIR / "assets" / "outreach_emails" / "prepared"
SENT_DIR = BASE_DIR / "assets" / "outreach_emails" / "sent"
LOG_PATH = BASE_DIR / "logs" / "outreach_run.log"

# SMTP Config
SMTP_HOST = os.environ.get("OUTREACH_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("OUTREACH_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("OUTREACH_SMTP_USER", "")
SMTP_PASS = os.environ.get("OUTREACH_SMTP_PASS", "")

# Rate limit
MAX_EMAILS_PER_RUN = 5


def log(message: str):
    """Log message to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_template() -> str:
    """Load email template."""
    if not TEMPLATE_PATH.exists():
        log(f"ERROR: Template not found: {TEMPLATE_PATH}")
        sys.exit(1)
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def load_recruiters() -> list:
    """Load recruiters from CSV."""
    if not CSV_PATH.exists():
        log(f"ERROR: CSV not found: {CSV_PATH}")
        sys.exit(1)
    
    recruiters = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            recruiters.append(row)
    return recruiters


def personalize_email(template: str, recruiter: dict) -> tuple:
    """Personalize email for recruiter. Returns (subject, body)."""
    body = template.replace("{name}", recruiter.get("name", "Hiring Manager"))
    body = body.replace("{company}", recruiter.get("company", "your company"))
    body = body.replace("{role}", recruiter.get("role", ""))
    
    # Extract subject from template (first line starting with Subject:)
    lines = body.split("\n")
    subject = "Open-Source AI Desktop Assistant — Bedanta Chatterjee"
    for line in lines:
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
            break
    
    # Remove subject line from body
    body = "\n".join(line for line in lines if not line.startswith("Subject:"))
    
    return subject, body.strip()


def prepare_emails(recruiters: list, template: str):
    """Generate personalized emails and save to prepared folder."""
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    
    for i, recruiter in enumerate(recruiters):
        subject, body = personalize_email(template, recruiter)
        
        filename = f"{i+1:03d}_{recruiter['company'].lower().replace(' ', '_')}.txt"
        filepath = PREPARED_DIR / filename
        
        content = f"""To: {recruiter['email']}
Subject: {subject}
---
{body}
"""
        filepath.write_text(content, encoding="utf-8")
        log(f"PREPARED: {filename} -> {recruiter['email']}")
    
    log(f"Total prepared: {len(recruiters)} emails in {PREPARED_DIR}")


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a single email via SMTP."""
    if not SMTP_USER or not SMTP_PASS:
        log("ERROR: SMTP credentials not set. Set OUTREACH_SMTP_USER and OUTREACH_SMTP_PASS")
        return False
    
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        return True
    except Exception as e:
        log(f"ERROR sending to {to_email}: {e}")
        return False


def send_emails(recruiters: list, template: str, dry_run: bool = False):
    """Send personalized emails (with rate limiting)."""
    SENT_DIR.mkdir(parents=True, exist_ok=True)
    
    sent_count = 0
    for recruiter in recruiters:
        if sent_count >= MAX_EMAILS_PER_RUN:
            log(f"Rate limit reached ({MAX_EMAILS_PER_RUN}/run). Run again tomorrow.")
            break
        
        subject, body = personalize_email(template, recruiter)
        
        if dry_run:
            log(f"DRY-RUN: Would send to {recruiter['email']}")
            continue
        
        if send_email(recruiter["email"], subject, body):
            sent_count += 1
            log(f"SENT: {recruiter['email']} ({sent_count}/{MAX_EMAILS_PER_RUN})")
            
            # Save copy to sent folder
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{recruiter['company']}.txt"
            (SENT_DIR / filename).write_text(f"To: {recruiter['email']}\n{body}", encoding="utf-8")
        else:
            log(f"FAILED: {recruiter['email']}")
    
    log(f"Session complete. Sent: {sent_count}/{len(recruiters)}")


def main():
    parser = argparse.ArgumentParser(description="Outreach Email Sender")
    parser.add_argument("--prepare", action="store_true", help="Prepare emails without sending")
    parser.add_argument("--send", action="store_true", help="Send emails (requires SMTP creds)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent")
    args = parser.parse_args()
    
    log("=" * 50)
    log("Outreach Email Sender Started")
    
    template = load_template()
    recruiters = load_recruiters()
    log(f"Loaded {len(recruiters)} recruiters from CSV")
    
    if args.prepare:
        prepare_emails(recruiters, template)
    elif args.send:
        send_emails(recruiters, template, dry_run=False)
    elif args.dry_run:
        send_emails(recruiters, template, dry_run=True)
    else:
        parser.print_help()
        log("No action specified. Use --prepare, --send, or --dry-run")
    
    log("Session ended")


if __name__ == "__main__":
    main()
