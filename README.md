# Bulk Mail Dashboard

A local Python dashboard to send personalized bulk email via your own SMTP server. Upload a CSV, preview the template, send to everyone with one click, and track sent vs rejected with retry support.

## Features

- CSV upload with flexible column names (`name`, `email`, `full_name`, etc.)
- Built-in HTML template (Jinja2) personalized per recipient
- Live metrics: Total, Sent, Rejected, Pending, Need to send again
- **Send to all** and **Retry rejected only**
- Download rejected recipients as CSV
- Professional Streamlit UI with custom theme

## Quick start

### 1. Prerequisites

- Python 3.10+
- An SMTP account (Gmail, Outlook, or custom)

### 2. Install

```bash
cd bulk-mail-dashboard
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 3. Configure SMTP

```bash
copy .env.example .env
```

Edit `.env` with your SMTP settings. For Gmail:

- Use an [App Password](https://support.google.com/accounts/answer/185833)
- `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USE_TLS=true`

### 4. Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## CSV format

```csv
name,email
Alice Johnson,alice@example.com
Bob Smith,bob@example.com
```

Invalid, duplicate, or empty rows are marked **skipped** and not sent.

## Project layout

```
app.py              # Streamlit UI
lib/                # config, csv, template, mailer, tracking, ui
templates/          # default.html email template
assets/style.css    # custom styles
docs/               # PROJECT_MANUAL.md
```

## Customize the template

Edit `templates/default.html` using Jinja2: `{{ name }}`, `{{ email }}`.

## Security

- Never commit `.env`
- Only email contacts who opted in
- Keep the app on localhost unless you add authentication

## Documentation

See [docs/PROJECT_MANUAL.md](docs/PROJECT_MANUAL.md) for the full presentation and user manual.
