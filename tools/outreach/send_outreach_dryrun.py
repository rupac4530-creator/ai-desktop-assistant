#!/usr/bin/env python3
"""
Outreach Dry-Run Validator
==========================
Validates prepared emails without sending.
Creates a detailed report of what WOULD be sent.

Author: Bedanta Chatterjee
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "outreach"
EMAILS_DIR = ASSETS_DIR / "prepared_emails"
LOGS_DIR = PROJECT_ROOT / "logs"

TARGETS_CSV = ASSETS_DIR / "targets.csv"
RECRUITERS_CSV = ASSETS_DIR / "recruiters_placeholder.csv"

# Create logs directory
LOGS_DIR.mkdir(exist_ok=True)

# Output files
LOG_FILE = LOGS_DIR / "outreach_dryrun.log"
REPORT_FILE = LOGS_DIR / "outreach_dryrun_report.json"


def log(message: str):
    """Log to both console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def load_targets() -> list:
    """Load targets.csv."""
    if not TARGETS_CSV.exists():
        log(f"ERROR: targets.csv not found at {TARGETS_CSV}")
        return []

    with open(TARGETS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_recruiters() -> dict:
    """Load recruiters_placeholder.csv as dict keyed by company."""
    if not RECRUITERS_CSV.exists():
        log(f"ERROR: recruiters_placeholder.csv not found at {RECRUITERS_CSV}")
        return {}

    recruiters = {}
    with open(RECRUITERS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            recruiters[row["company"].lower()] = row
    return recruiters


def load_prepared_emails() -> dict:
    """Load all prepared email files."""
    emails = {}
    if not EMAILS_DIR.exists():
        log(f"ERROR: prepared_emails directory not found at {EMAILS_DIR}")
        return {}

    for email_file in EMAILS_DIR.glob("*.txt"):
        company_key = email_file.stem.lower()
        with open(email_file, "r", encoding="utf-8") as f:
            emails[company_key] = f.read()
    return emails


def validate_email_content(content: str, company: str) -> list:
    """Validate email content for issues."""
    issues = []

    # Check for placeholder artifacts
    if "{" in content and "}" in content:
        placeholders = re.findall(r"\{[^}]+\}", content)
        if placeholders:
            issues.append(f"Unfilled placeholders found: {placeholders}")

    # Check for minimum length
    if len(content) < 500:
        issues.append(f"Email too short ({len(content)} chars, expected 500+)")

    # Check for key components
    required_patterns = [
        (r"github\.com", "GitHub link missing"),
        (r"bedanta|chatterjee", "Author name missing"),
        (r"ai.?desktop|voice.?assistant", "Project name missing"),
    ]

    content_lower = content.lower()
    for pattern, error in required_patterns:
        if not re.search(pattern, content_lower):
            issues.append(error)

    return issues


def run_dryrun():
    """Main dry-run function."""
    log("=" * 60)
    log("OUTREACH DRY-RUN VALIDATOR")
    log("=" * 60)

    # Load data
    targets = load_targets()
    recruiters = load_recruiters()
    prepared_emails = load_prepared_emails()

    log(f"Loaded {len(targets)} target companies")
    log(f"Loaded {len(recruiters)} recruiter entries")
    log(f"Loaded {len(prepared_emails)} prepared emails")
    log("-" * 60)

    # Validation results
    results = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_targets": len(targets),
            "emails_prepared": len(prepared_emails),
            "emails_ready_to_send": 0,
            "emails_missing_contact": 0,
            "emails_with_issues": 0,
        },
        "ready_to_send": [],
        "missing_contact": [],
        "validation_issues": [],
        "no_prepared_email": [],
    }

    for target in targets:
        company = target["company"]
        company_key = company.lower().replace(" ", "").replace("-", "")

        # Check if we have a prepared email
        email_content = None
        for key, content in prepared_emails.items():
            if key in company_key or company_key in key:
                email_content = content
                break

        # Check recruiter info
        recruiter = recruiters.get(company.lower())
        has_email = recruiter and recruiter.get("contact_email") and validate_email(recruiter.get("contact_email", ""))

        if not email_content:
            results["no_prepared_email"].append(
                {"company": company, "region": target.get("region", "Unknown"), "note": "Use generic template"}
            )
            continue

        # Validate email content
        issues = validate_email_content(email_content, company)

        if issues:
            results["validation_issues"].append({"company": company, "issues": issues})
            results["summary"]["emails_with_issues"] += 1
        elif not has_email:
            results["missing_contact"].append(
                {
                    "company": company,
                    "region": target.get("region", "Unknown"),
                    "recruiter_name": recruiter.get("contact_name", "Unknown") if recruiter else "None",
                    "linkedin": recruiter.get("contact_linkedin", "None") if recruiter else "None",
                }
            )
            results["summary"]["emails_missing_contact"] += 1
        else:
            results["ready_to_send"].append(
                {
                    "company": company,
                    "contact_name": recruiter.get("contact_name"),
                    "contact_email": recruiter.get("contact_email"),
                    "email_preview": email_content[:200] + "...",
                }
            )
            results["summary"]["emails_ready_to_send"] += 1

    # Print summary
    log("\n" + "=" * 60)
    log("DRY-RUN SUMMARY")
    log("=" * 60)
    log(f"Total target companies: {results['summary']['total_targets']}")
    log(f"Prepared emails: {results['summary']['emails_prepared']}")
    log(f"Ready to send (have email): {results['summary']['emails_ready_to_send']}")
    log(f"Missing contact email: {results['summary']['emails_missing_contact']}")
    log(f"Emails with issues: {results['summary']['emails_with_issues']}")
    log(f"No prepared email (use generic): {len(results['no_prepared_email'])}")

    if results["validation_issues"]:
        log("\n⚠️  EMAILS WITH ISSUES:")
        for item in results["validation_issues"]:
            log(f"  - {item['company']}: {', '.join(item['issues'])}")

    if results["ready_to_send"]:
        log("\n✅ READY TO SEND (once you add recruiter emails):")
        for item in results["ready_to_send"]:
            log(f"  - {item['company']} → {item['contact_email']}")

    if results["missing_contact"]:
        log("\n⏳ NEED RECRUITER EMAIL:")
        for item in results["missing_contact"]:
            log(f"  - {item['company']} ({item['region']})")
            if item["linkedin"] != "None":
                log(f"    LinkedIn: {item['linkedin']}")

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    log(f"\n📄 Full report saved to: {REPORT_FILE}")

    # Final status
    log("\n" + "=" * 60)
    if results["summary"]["emails_ready_to_send"] > 0:
        log("✅ DRY-RUN PASSED - Some emails ready to send")
        log("   Run 'python tools/send_outreach.py --send' to send")
    else:
        log("⚠️  DRY-RUN INCOMPLETE - Need to add recruiter emails")
        log("   Update assets/outreach/recruiters_placeholder.csv")
    log("=" * 60)

    return results


if __name__ == "__main__":
    try:
        run_dryrun()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
