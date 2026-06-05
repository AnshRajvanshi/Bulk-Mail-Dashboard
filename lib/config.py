"""Load SMTP and app settings from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_user: str
    smtp_pass: str
    mail_from: str
    default_subject: str
    throttle_seconds: float

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass and self.mail_from)


def _bool_env(key: str, default: bool = True) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes", "on")


def load_settings() -> Settings:
    return Settings(
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_use_tls=_bool_env("SMTP_USE_TLS", True),
        smtp_user=os.getenv("SMTP_USER", "").strip(),
        smtp_pass=os.getenv("SMTP_PASS", "").strip(),
        mail_from=os.getenv("MAIL_FROM", "").strip(),
        default_subject=os.getenv("DEFAULT_SUBJECT", "Message from Bulk Mail Dashboard").strip(),
        throttle_seconds=float(os.getenv("THROTTLE_SECONDS", "1.5")),
    )
