"""Parse and validate uploaded CSV recipient files."""

from __future__ import annotations

import re
from io import BytesIO, StringIO

import pandas as pd

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

NAME_HEADERS = {"name", "full_name", "fullname", "full name", "recipient", "recipient_name"}
EMAIL_HEADERS = {"email", "e-mail", "e_mail", "mail", "email_address", "email address"}

RECIPIENT_COLUMNS = ["name", "email", "status", "error", "sent_at"]


def _normalize_header(h: str) -> str:
    return re.sub(r"[\s_-]+", " ", str(h).strip().lower())


def _map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame | None, str | None]:
    col_map = {_normalize_header(c): c for c in df.columns}
    name_col = next((col_map[h] for h in NAME_HEADERS if h in col_map), None)
    email_col = next((col_map[h] for h in EMAIL_HEADERS if h in col_map), None)

    if not name_col or not email_col:
        return None, "CSV must include name and email columns (e.g. name, email)."

    out = df[[name_col, email_col]].copy()
    out.columns = ["name", "email"]
    return out, None


def _valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def parse_csv(file_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Parse CSV bytes into valid sendable rows and skipped rows.

    Returns (valid_df, skipped_df, stats).
    """
    try:
        raw = pd.read_csv(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Could not read CSV: {exc}") from exc

    if raw.empty:
        raise ValueError("CSV file is empty.")

    mapped, err = _map_columns(raw)
    if err or mapped is None:
        raise ValueError(err or "Invalid CSV columns.")

    mapped["name"] = mapped["name"].astype(str).str.strip()
    mapped["email"] = mapped["email"].astype(str).str.strip().str.lower()

    rows = []
    seen_emails: set[str] = set()

    for _, row in mapped.iterrows():
        name, email = row["name"], row["email"]
        reason = None

        if not name or name.lower() == "nan":
            reason = "Missing name"
        elif not email or email == "nan":
            reason = "Missing email"
        elif not _valid_email(email):
            reason = "Invalid email format"
        elif email in seen_emails:
            reason = "Duplicate email"
        else:
            seen_emails.add(email)

        rows.append(
            {
                "name": name if name and name.lower() != "nan" else "",
                "email": email if email and email != "nan" else "",
                "status": "skipped" if reason else "pending",
                "error": reason or "",
                "sent_at": "",
            }
        )

    full = pd.DataFrame(rows)
    skipped = full[full["status"] == "skipped"].copy()
    valid = full[full["status"] != "skipped"].copy().reset_index(drop=True)

    stats = {
        "total_rows": len(full),
        "valid": len(valid),
        "skipped": len(skipped),
    }
    return valid, skipped, stats


def recipients_to_csv_bytes(df: pd.DataFrame) -> bytes:
    export = df.copy()
    for col in RECIPIENT_COLUMNS:
        if col not in export.columns:
            export[col] = ""
    export = export[RECIPIENT_COLUMNS]
    buf = StringIO()
    export.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
