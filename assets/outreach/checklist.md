# 📋 Outreach Checklist & Action Plan

## Author: Bedanta Chatterjee
## Email: rupac4530@gmail.com
## Phone: +91 8617513035
## GitHub: https://github.com/rupac4530-creator/ai-desktop-assistant

---

## 🎯 TARGET SUMMARY

| Region | Companies | Priority |
|--------|-----------|----------|
| **USA** | 15 | High (Big Tech + AI) |
| **Dubai/UAE** | 10 | Medium (Regional hubs) |
| **Singapore** | 13 | Medium (APAC hubs) |
| **TOTAL** | 38 | Start with 10-15 |

---

## ✅ PRE-OUTREACH CHECKLIST

### 1. Project Ready
- [x] GitHub repo public and polished
- [x] README recruiter-optimized
- [x] Release v1.0.1 with ZIP attached
- [x] Demo screenshot in assets/
- [ ] **Record 90-second demo video** (REQUIRED)
- [ ] **Upload to YouTube (unlisted)**
- [ ] **Create one-pager PDF** (docs/onepager.html → print to PDF)

### 2. Outreach Assets Ready
- [x] targets.csv created (38 companies)
- [x] recruiters_placeholder.csv created
- [x] Email templates created (generic + company-specific)
- [x] LinkedIn posts created (3 versions)
- [x] InMail templates created
- [ ] **Fill recruiters_placeholder.csv with real contacts** (you do this)

### 3. Accounts Ready
- [ ] **LinkedIn profile updated** (headline: "AI/ML Developer | Open-Source")
- [ ] **LinkedIn "Open to Work" enabled**
- [ ] **Gmail app password created** (for SMTP sending)

---

## 📧 EMAIL SENDING PLAN

### Phase 1: Week 1 (5 emails/day)
| Day | Companies | Region |
|-----|-----------|--------|
| Mon | Google, Microsoft, OpenAI | USA |
| Tue | NVIDIA, GitHub | USA |
| Wed | G42, Dubai Future Foundation | Dubai |
| Thu | Grab, GovTech Singapore | Singapore |
| Fri | Meta, Amazon | USA |

### Phase 2: Week 2 (5 emails/day)
| Day | Companies | Region |
|-----|-----------|--------|
| Mon | Hugging Face, Anthropic, Stripe | USA |
| Tue | Careem, Noon, Emirates | Dubai |
| Wed | Sea Group, DBS, AWS Singapore | Singapore |
| Thu | Apple, Salesforce, Adobe | USA |
| Fri | Follow-ups from Week 1 | All |

### Follow-up Schedule
- **Day 7**: Polite follow-up if no response
- **Day 14**: Final follow-up (shorter, with demo video link)
- **Day 21**: Mark as "No Response" and move on

---

## 📱 LINKEDIN OUTREACH PLAN

### Daily Actions (15-20 mins/day)
1. Post content (3x per week per schedule)
2. Send 5-10 connection requests to target company employees
3. Reply to all comments on your posts
4. Check InMail and respond within 24 hours

### Connection Request Priority
1. Technical Recruiters at target companies
2. Engineering Managers (AI/Platform/Tools teams)
3. Developers at target companies (for referrals)

### What NOT to do
- ❌ Send generic mass requests (LinkedIn will restrict you)
- ❌ Message immediately after connecting (wait 1-2 days)
- ❌ Use automation tools (risk of ban)

---

## 📁 FILE LOCATIONS

| File | Purpose | Status |
|------|---------|--------|
| `assets/outreach/targets.csv` | Company list | ✅ Ready |
| `assets/outreach/recruiters_placeholder.csv` | Contact list | ⏳ Need real emails |
| `assets/outreach/prepared_emails/*.txt` | Email drafts | ✅ Ready |
| `assets/outreach/linkedin_posts.txt` | LinkedIn content | ✅ Ready |
| `assets/outreach/inmail_templates.txt` | DM templates | ✅ Ready |
| `tools/outreach/send_outreach_dryrun.py` | Dry-run sender | ✅ Ready |
| `logs/outreach_sent.csv` | Send log | ⏳ Create when sending |

---

## 🔧 MANUAL STEPS (YOU MUST DO)

### Step 1: Record Demo Video (30 mins)
```
1. Follow assets/demo_script.txt
2. Use OBS or ShareX to record
3. Keep under 90 seconds
4. Upload to YouTube as UNLISTED
5. Copy link and add to emails
```

### Step 2: Find Recruiter Emails (1-2 hours)
```
For each target company:
1. Go to company LinkedIn page → People → Search "recruiter" or "talent"
2. Find 1-2 relevant contacts
3. Check their LinkedIn for email (some show it publicly)
4. Or use company careers page contact form
5. Add to recruiters_placeholder.csv
```

### Step 3: Set Up Gmail SMTP (10 mins)
```
1. Go to Google Account → Security → 2FA (enable if not)
2. App Passwords → Generate new password for "Mail"
3. Save the 16-character password
4. Set environment variables:
   $env:OUTREACH_SMTP_HOST = "smtp.gmail.com"
   $env:OUTREACH_SMTP_USER = "rupac4530@gmail.com"
   $env:OUTREACH_SMTP_PASS = "your-app-password"
```

### Step 4: Update LinkedIn Profile (15 mins)
```
1. Headline: "AI/ML Developer | Building Open-Source AI Tools | Python, Whisper, LLMs"
2. About: Add project description and demo link
3. Featured: Add GitHub repo link and demo video
4. Open to Work: Enable for USA, UAE, Singapore
```

### Step 5: Run Dry-Run Test (5 mins)
```powershell
cd E:\ai_desktop_assistant
python tools/outreach/send_outreach_dryrun.py
# Check logs/outreach_dryrun.log
```

### Step 6: Send First Batch (With Approval)
```powershell
# Only after dry-run passes and you approve
$env:OUTREACH_SMTP_HOST = "smtp.gmail.com"
$env:OUTREACH_SMTP_USER = "rupac4530@gmail.com"
$env:OUTREACH_SMTP_PASS = "your-app-password"
python tools/send_outreach.py --send
```

---

## 📊 TRACKING TEMPLATE

Create `logs/outreach_sent.csv` with:
```csv
date,company,contact_name,contact_email,method,status,notes
2026-01-20,Google,John Doe,john@google.com,email,sent,Follow up Jan 27
```

---

## 🎯 SUCCESS METRICS

| Metric | Target |
|--------|--------|
| Emails sent | 30-40 |
| Response rate | 10-20% (3-8 responses) |
| Demo calls | 2-4 |
| Interviews | 1-2 |

---

## ⚠️ IMPORTANT NOTES

1. **Quality over quantity** — Personalized emails get 3x more responses
2. **Don't spam** — 5 emails/day max, follow-up once only
3. **Track everything** — Log every send in outreach_sent.csv
4. **Be patient** — Recruiters take 3-7 days to respond
5. **If no response** — Move on after 2 follow-ups

---

## 🚀 QUICK START (Do These 5 Things Today)

1. ⬜ Record 90-second demo video
2. ⬜ Update LinkedIn profile with "Open to Work"
3. ⬜ Find 5 recruiter emails from target companies
4. ⬜ Set up Gmail app password
5. ⬜ Run dry-run test

**Once ready, say: "OK SEND 5" and provide SMTP credentials**
