"""Bulk Mail Dashboard — Streamlit entrypoint."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from lib.config import load_settings
from lib.csv_loader import parse_csv, recipients_to_csv_bytes
from lib.mailer import send_batch
from lib.template import render_template
from lib.tracking import compute_summary, get_rejected_df, get_sendable_indices
from lib.ui import (
    email_preview_html,
    empty_state_upload,
    inject_css,
    metric_cards,
    render_header,
    render_sidebar,
    section_title,
    success_banner,
)

st.set_page_config(
    page_title="Bulk Mail Dashboard",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
settings = load_settings()
ROOT = Path(__file__).resolve().parent
manual_path = str(ROOT / "docs" / "PROJECT_MANUAL.md")

render_sidebar(settings.smtp_configured, manual_path)
render_header()

if "recipients" not in st.session_state:
    st.session_state.recipients = None
if "skipped" not in st.session_state:
    st.session_state.skipped = None
if "upload_stats" not in st.session_state:
    st.session_state.upload_stats = None
if "sending" not in st.session_state:
    st.session_state.sending = False
if "subject" not in st.session_state:
    st.session_state.subject = settings.default_subject
if "send_complete" not in st.session_state:
    st.session_state.send_complete = False

# --- Upload ---
section_title("📁 Upload recipients", "CSV with name and email columns")
uploaded = st.file_uploader(
    "Choose CSV file",
    type=["csv"],
    help="Accepted headers: name, email, full_name, e-mail, etc.",
)
# Attach file
section_title("📎 Attach Resume (optional)", "PDF attached to every email")
uploaded_resume = st.file_uploader(
    "Upload your resume PDF",
    type=["pdf"],
    help="Will be attached to every outgoing email.",
    key="resume_uploader",
)

if uploaded_resume is not None:
    st.session_state.resume_bytes = uploaded_resume.read()
    st.session_state.resume_filename = uploaded_resume.name
    st.success(f"Resume attached: **{uploaded_resume.name}**")
elif "resume_bytes" not in st.session_state:
    st.session_state.resume_bytes = None
    st.session_state.resume_filename = None

if uploaded is not None:
    try:
        valid, skipped, stats = parse_csv(uploaded.getvalue())
        st.session_state.recipients = valid
        st.session_state.skipped = skipped
        st.session_state.upload_stats = stats
        st.session_state.send_complete = False   # ← reset on new upload
        st.success(
            f"Loaded **{stats['valid']}** valid recipients "
            f"({stats['skipped']} skipped)."
        )
    except ValueError as exc:
        st.error(str(exc))

recipients: pd.DataFrame | None = st.session_state.recipients

if recipients is None or recipients.empty:
    empty_state_upload()
    st.stop()

# --- Upload stats ---
stats = st.session_state.upload_stats or {}
c1, c2, c3 = st.columns(3)
c1.metric("Valid recipients", stats.get("valid", len(recipients)))
c2.metric("Skipped rows", stats.get("skipped", 0))
c3.metric("Ready to send", int((recipients["status"] == "pending").sum()))

# --- Tracking ---
section_title("📊 Send tracking", "Live counts during and after each run")
summary = compute_summary(recipients)
metric_cards(summary)

# --- Subject & template ---
section_title("✉️ Email content")
subject = st.text_input(
    "Subject line",
    value=st.session_state.subject,
    disabled=st.session_state.sending,
)
st.session_state.subject = subject

with st.expander("Preview template", expanded=False):
    first = recipients.iloc[0]
    preview_html = render_template(name=str(first["name"]), email=str(first["email"]))
    st.caption(f"Preview for: {first['name']} <{first['email']}>")
    email_preview_html(preview_html)

# --- Recipients table ---
section_title("👥 Recipients")
display_df = recipients.copy()
display_df["status"] = display_df["status"].astype(str)

st.dataframe(
    display_df,
    use_container_width=True,
    height=360,
    hide_index=True,
    column_config={
        "status": st.column_config.TextColumn("Status", width="small"),
        "error": st.column_config.TextColumn("Error", width="medium"),
        "sent_at": st.column_config.TextColumn("Sent at", width="medium"),
    },
)

# --- Send / retry actions ---
st.divider()
progress_slot = st.empty()
caption_slot = st.empty()

pending_count = int((recipients["status"] == "pending").sum())
rejected_count = int((recipients["status"] == "rejected").sum())
can_send_all = pending_count > 0 and not st.session_state.sending and settings.smtp_configured
can_retry = rejected_count > 0 and not st.session_state.sending and settings.smtp_configured

col_send, col_retry = st.columns([2, 1])

with col_send:
    send_all = st.button(
        "🚀 Send to all",
        type="primary",
        use_container_width=True,
        disabled=not can_send_all,
    )

with col_retry:
    retry_rejected = st.button(
        "↻ Retry rejected only",
        use_container_width=True,
        disabled=not can_retry,
    )

rejected_df = get_rejected_df(recipients)
if not rejected_df.empty:
    st.download_button(
        label="⬇️ Download rejected",
        data=recipients_to_csv_bytes(rejected_df),
        file_name="rejected_recipients.csv",
        mime="text/csv",
        use_container_width=False,
    )

if not settings.smtp_configured:
    st.warning("Configure SMTP in `.env` before sending. See README for Gmail app password steps.")


def run_send(indices: list[int], label: str) -> None:
    st.session_state.sending = True
    total = len(indices)
    bar = progress_slot.progress(0.0)
    caption_slot.caption(f"{label} 0 of {total}…")

    def on_progress(done: int, batch_total: int, summ: dict) -> None:
        bar.progress(done / batch_total if batch_total else 0.0)
        caption_slot.caption(f"{label} {done} of {batch_total}…")
        metric_cards(summ)

    try:
        send_batch(
            settings,
            st.session_state.recipients,
            indices,
            st.session_state.subject,
            on_progress=on_progress,
            resume_bytes=st.session_state.get("resume_bytes"),        # ← new
            resume_filename=st.session_state.get("resume_filename"),  # ← new
        )
    finally:
        st.session_state.sending = False
        st.session_state.send_complete = True
        progress_slot.progress(1.0)
        final = compute_summary(st.session_state.recipients)
        metric_cards(final)
        if final["rejected"] == 0 and final["pending"] == 0 and final["sent"] > 0:
            success_banner(f"All {final['sent']} emails sent successfully.")
        elif final["rejected"] > 0:
            st.warning(
                f"{final['rejected']} rejected — use **Retry rejected only** or download the CSV."
            )
        st.rerun()


if send_all:
    indices = get_sendable_indices(recipients, only_rejected=False)
    pending_only = [i for i in indices if st.session_state.recipients.loc[i, "status"] == "pending"]
    run_send(pending_only, "Sending")

if retry_rejected:
    indices = get_sendable_indices(recipients, only_rejected=True)
    run_send(indices, "Retrying")

# Success state when complete with no rejections
if recipients is not None and not st.session_state.sending:
    final = compute_summary(recipients)
    if final["total"] > 0 and final["pending"] == 0 and final["rejected"] == 0 and final["sent"] == final["total"]:
        success_banner("Batch complete — no emails need to be sent again.")
