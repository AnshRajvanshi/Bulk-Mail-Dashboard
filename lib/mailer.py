"""SMTP email sending with throttle and retry."""

from __future__ import annotations
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Callable

import html2text

from lib.config import Settings
from lib.template import render_template


def html_to_plain(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.body_width = 0
    return converter.handle(html).strip()


def build_message(
    settings: Settings,
    to_email: str,
    subject: str,
    html_body: str,
    resume_bytes: bytes | None = None,
    resume_filename: str | None = None,
) -> MIMEMultipart:
    # Outer container must be "mixed" when there's an attachment
    outer = MIMEMultipart("mixed")
    outer["Subject"] = subject
    outer["From"] = settings.mail_from
    outer["To"] = to_email

    # Inner alternative part holds plain + html
    alt = MIMEMultipart("alternative")
    plain = html_to_plain(html_body)
    alt.attach(MIMEText(plain, "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    outer.attach(alt)

    # Attach PDF resume if provided
    if resume_bytes and resume_filename:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(resume_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{resume_filename}"',
        )
        part.add_header("Content-Type", "application/pdf")
        outer.attach(part)

    return outer


def _send_once(settings: Settings, msg: MIMEMultipart, to_email: str) -> None:
    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.mail_from, [to_email], msg.as_string())
    else:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.mail_from, [to_email], msg.as_string())


def send_email(
    settings: Settings,
    to_email: str,
    subject: str,
    name: str,
    email: str,
    resume_bytes: bytes | None = None,
    resume_filename: str | None = None,
) -> None:
    if not settings.smtp_configured:
        raise RuntimeError(
            "SMTP is not configured. Copy .env.example to .env and fill in your credentials."
        )

    html_body = render_template(name=name, email=email)
    msg = build_message(
        settings, to_email, subject, html_body,
        resume_bytes=resume_bytes,
        resume_filename=resume_filename,
    )

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            _send_once(settings, msg, to_email)
            return
        except smtplib.SMTPException as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(0.5)
        except OSError as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(0.5)

    raise RuntimeError(str(last_error) if last_error else "Unknown SMTP error")


def send_batch(
    settings: Settings,
    df,
    indices: list[int],
    subject: str,
    on_progress: Callable[[int, int, dict], None] | None = None,
    throttle: bool = True,
    resume_bytes: bytes | None = None,       # ← new
    resume_filename: str | None = None,      # ← new
) -> None:
    total = len(indices)
    for i, idx in enumerate(indices):
        row = df.loc[idx]
        name = str(row["name"])
        email = str(row["email"])

        try:
            send_email(
                settings, email, subject, name, email,
                resume_bytes=resume_bytes,
                resume_filename=resume_filename,
            )
            df.at[idx, "status"] = "sent"
            df.at[idx, "error"] = ""
            df.at[idx, "sent_at"] = pd_timestamp_now()
        except Exception as exc:
            df.at[idx, "status"] = "rejected"
            df.at[idx, "error"] = str(exc)[:500]
            df.at[idx, "sent_at"] = ""

        if on_progress:
            from lib.tracking import compute_summary
            on_progress(i + 1, total, compute_summary(df))

        if throttle and i < total - 1:
            time.sleep(settings.throttle_seconds)


def pd_timestamp_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
