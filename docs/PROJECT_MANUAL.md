# Bulk Mail Dashboard — Project Manual & Presentation Document

**Version:** 1.0 (pre-build specification)  
**Date:** June 5, 2026  
**Audience:** Stakeholders, presenters, and end users  
**Deployment:** Local solo use (your computer)

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Problem we are solving](#2-problem-we-are-solving)
3. [What we will build (features)](#3-what-we-will-build-features)
4. [Technology stack](#4-technology-stack)
5. [System architecture](#5-system-architecture)
6. [End-to-end user workflow](#6-end-to-end-user-workflow)
7. [CSV file format](#7-csv-file-format)
8. [Email template](#8-email-template)
9. [Send tracking and metrics](#9-send-tracking-and-metrics)
10. [SMTP configuration](#10-smtp-configuration)
11. [Security and compliance](#11-security-and-compliance)
12. [Project structure](#12-project-structure)
13. [Implementation phases](#13-implementation-phases)
14. [Success criteria](#14-success-criteria)
15. [Risks and limitations](#15-risks-and-limitations)
16. [Future enhancements](#16-future-enhancements)

---

## 1. Executive summary

The **Bulk Mail Dashboard** is a Python web application that lets you send personalized emails to many people from a single screen. You upload a spreadsheet (CSV) with names and email addresses, review a built-in HTML template, and press **Send to all**. The system sends one personalized email per person through your own SMTP account (Gmail, Outlook, or any SMTP server).

During and after each run, the dashboard shows how many emails were **sent**, how many were **rejected**, and how many **need to be sent again**, so you can retry failures without re-uploading the full list.

---

## 2. Problem we are solving

| Today (manual) | With this dashboard |
|----------------|---------------------|
| Copy-paste names into email one by one | Upload one CSV file |
| Risk of wrong template or missed people | One shared template, full recipient list visible |
| No clear count of failures | Live **Sent / Rejected / Need to send again** metrics |
| Hard to resend only failed addresses | **Retry rejected only** button + download failed rows |

---

## 3. What we will build (features)

### 3.1 Core features (Version 1)

1. **CSV upload** — Upload a file with recipient `name` and `email` columns (flexible header names supported).
2. **Validation** — Invalid emails, duplicates, and empty rows are flagged as **skipped** before sending.
3. **Recipient preview** — Table of all valid recipients before you send.
4. **Built-in email template** — One HTML template on disk, personalized per person (`Hi {{ name }}, …`).
5. **Template preview** — See how the email looks for the first recipient before sending.
6. **Editable subject line** — Set the email subject on the dashboard (with a default from config).
7. **Send to all** — One button starts the full batch after upload.
8. **Live send tracking** — Five counters update as each email is processed:
   - **Total**
   - **Sent**
   - **Rejected**
   - **Pending**
   - **Need to send again**
9. **Per-row status** — Each row shows `pending`, `sent`, `rejected`, or `skipped`, plus an error message if rejected.
10. **Progress bar** — Visual progress during the send (e.g. 45 / 100 sent).
11. **Automatic retry** — One automatic retry per failed SMTP attempt before marking as rejected.
12. **Throttle** — Pause between emails (configurable) to reduce SMTP blocks and rate limits.
13. **Retry rejected only** — Resend only failed rows without re-uploading the CSV.
14. **Download rejected** — Export failed rows as CSV for fixes or re-upload.

### 3.2 Not included in Version 1

- User login / multi-user accounts
- Drag-and-drop template editor in the UI
- Open/click tracking analytics
- Scheduled sends
- File attachments
- Public internet hosting (designed for local use first)

---

## 4. Technology stack

| Component | Technology | Role |
|-----------|------------|------|
| **Language** | Python 3.10+ | Entire application |
| **User interface** | Streamlit | Dashboard in the browser |
| **Data handling** | pandas | Parse and display CSV data |
| **Email templates** | Jinja2 | Personalize HTML per recipient |
| **Email delivery** | smtplib + email.mime (stdlib) | Send via your SMTP server |
| **Configuration** | python-dotenv | SMTP credentials in `.env` |
| **Plain-text emails** | html2text (optional) | HTML + text multipart for deliverability |

**How you will run it (after build):**

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501` (default).

---

## 5. System architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser   │────▶│  Streamlit app   │────▶│  templates/     │
│  (Dashboard)│     │     (app.py)     │     │  default.html   │
└─────────────┘     └────────┬─────────┘     └─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        csv_loader    template.py     mailer.py
              │              │              │
              └──────────────┴──────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Your SMTP     │
                    │  (Gmail, etc.) │
                    └────────────────┘
```

**Design choice:** Everything runs in one Python process on your machine. No separate database server or cloud email API is required for Version 1.

---

## 6. End-to-end user workflow

### Step-by-step (user manual)

| Step | Action | What you see |
|------|--------|--------------|
| 1 | Start the app | Dashboard home screen |
| 2 | Upload CSV | Parsed recipient table |
| 3 | Check valid vs skipped | Count of rows ready to send |
| 4 | Open template preview | Sample email for first valid person |
| 5 | Edit subject if needed | Subject applied to whole batch |
| 6 | Click **Send to all** | Progress bar + live metrics |
| 7 | Wait for completion | Final Sent / Rejected / Need to send again |
| 8 | If rejections exist | Use **Retry rejected only** or **Download rejected** |

### Flow diagram

```
Upload CSV → Validate → Preview template → Send to all
                ↓                              ↓
           Show skipped              Update Sent / Rejected / Pending
                                                ↓
                                    Need to send again > 0?
                                                ↓
                              Retry rejected only  OR  Download CSV
```

---

## 7. CSV file format

**Required data:** Each row must have a **name** and **email**.

**Accepted column headers (examples):**

| Name column | Email column |
|-------------|--------------|
| `name` | `email` |
| `full_name` | `e-mail` |
| `Name` | `Email` |

**Example CSV:**

```csv
name,email
Alice Johnson,alice@example.com
Bob Smith,bob@example.com
```

**Validation rules:**

- Email must be a valid format
- Duplicate emails in the same file are **skipped**
- Empty name or email rows are **skipped**
- Skipped rows do not count toward send totals

---

## 8. Email template

- **Location:** `templates/default.html`
- **Engine:** Jinja2 placeholders `{{ name }}`, `{{ email }}`
- **Behavior:** Same layout for everyone; only name and email change per message
- **Editing (v1):** Edit the HTML file directly; UI editor is a future enhancement

**Example template body:**

```html
<p>Hi {{ name }},</p>
<p>Your message here…</p>
<p>— Team</p>
```

Each recipient receives an **individual email** (not one BCC blast), which is required for personalization.

---

## 9. Send tracking and metrics

### 9.1 Summary counters (top of dashboard)

| Metric | Meaning |
|--------|---------|
| **Total** | Number of valid recipients in the batch |
| **Sent** | Successfully delivered via SMTP |
| **Rejected** | Failed after automatic retry |
| **Pending** | Not yet attempted in the current run |
| **Need to send again** | How many must be retried (equals Rejected when the run is finished) |

**Rule during sending:** `Sent + Rejected + Pending = Total`

### 9.2 Per-row columns in the table

| Column | Description |
|--------|-------------|
| `name` | From CSV |
| `email` | From CSV |
| `status` | `pending`, `sent`, `rejected`, or `skipped` |
| `error` | SMTP or error details if rejected |
| `sent_at` | Timestamp when sent (optional audit field) |

### 9.3 Retry workflow

1. Batch finishes with some **Rejected** rows.
2. **Need to send again** shows the count.
3. Fix issues if needed (wrong address, SMTP limits).
4. Click **Retry rejected only** — only failed rows are resent.
5. Or **Download rejected** CSV, fix offline, and re-upload if preferred.

---

## 10. SMTP configuration

Credentials are stored locally in a `.env` file (not committed to git).

| Setting | Example | Purpose |
|---------|---------|---------|
| `SMTP_HOST` | `smtp.gmail.com` | Mail server |
| `SMTP_PORT` | `587` | Port (TLS) |
| `SMTP_USE_TLS` | `true` | Secure connection |
| `SMTP_USER` | `you@example.com` | Login |
| `SMTP_PASS` | app password | Secret |
| `MAIL_FROM` | `Your Name <you@example.com>` | From address |
| `DEFAULT_SUBJECT` | `Your subject` | Default subject line |
| `THROTTLE_SECONDS` | `1.5` | Delay between sends |

**Setup notes:**

- Gmail and Outlook typically require an **app password**, not your normal login password.
- Providers enforce **daily send limits** (especially free accounts).
- Throttling helps avoid temporary blocks but does not remove provider limits.

---

## 11. Security and compliance

| Topic | Approach |
|-------|----------|
| **Secrets** | `.env` file gitignored; example file has placeholders only |
| **Access** | Localhost by default; no login in Version 1 |
| **Consent** | Only send to people who agreed to receive mail |
| **Legal** | Unsolicited bulk mail may violate CAN-SPAM/GDPR and get accounts blocked |

---

## 12. Project structure

```
bulk-mail-dashboard/
├── app.py                 # Main dashboard (Streamlit)
├── lib/
│   ├── config.py          # Load .env settings
│   ├── csv_loader.py      # Parse and validate CSV
│   ├── template.py        # Jinja2 render
│   ├── mailer.py          # SMTP send + throttle
│   └── tracking.py        # Counters and retry helpers
├── templates/
│   └── default.html       # Email template
├── docs/
│   └── PROJECT_MANUAL.md  # This document
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md              # Quick start guide
```

---

## 13. Implementation phases

| Phase | Deliverable |
|-------|-------------|
| 1 | Project scaffold, dependencies, README, this manual |
| 2 | CSV upload, validation, recipient table |
| 3 | Template preview and subject line |
| 4 | SMTP sending with throttle and auto-retry |
| 5 | Live tracking metrics and progress bar |
| 6 | Retry rejected + download rejected CSV |
| 7 | Test with real SMTP (2–3 test addresses first) |

---

## 14. Success criteria

- User can upload CSV and see all valid recipients within seconds
- User can preview personalized template before sending
- **Send to all** sends one personalized email per row via SMTP
- **Sent**, **Rejected**, and **Need to send again** update during the run
- **Retry rejected only** resends only failed rows
- Rejected rows can be downloaded as CSV
- No passwords or secrets stored in source control

---

## 15. Risks and limitations

| Risk | Mitigation |
|------|------------|
| SMTP daily limits | Show counts; throttle; document limits in README |
| Account lockout / spam flags | Throttle; send to opted-in lists only |
| Large lists (1000+) | May take time due to throttle; progress bar shows status |
| Long runs in browser | Session state preserves per-row status |

---

## 16. Future enhancements (after Version 1)

- Template editor in the UI
- Send history stored in SQLite
- Scheduled campaigns
- Attachment support
- Team login and roles
- Transactional email API (SendGrid, AWS SES) for higher volume

---

## 17. Professional user interface

The built application includes a polished Streamlit experience:

- Custom theme (teal accent, light background) in `.streamlit/config.toml`
- Metric cards for Total, Sent, Rejected, Pending, Need to send again
- Sidebar with setup steps and SMTP status indicator
- Empty state before CSV upload; success banner when batch completes
- Inbox-style template preview and bordered recipient table

---

## Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | June 5, 2026 | Initial specification for presentation and build |
| 1.1 | June 5, 2026 | Added UI section; application implemented |

---

*End of document*
