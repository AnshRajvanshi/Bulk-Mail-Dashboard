"""Streamlit UI helpers — theme, layout, metric cards."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / "assets" / "style.css"


def inject_css() -> None:
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
          <h1>📬 Bulk Mail Dashboard</h1>
        </div>
        <p class="app-subtitle">
          Upload recipients, preview your template, and send personalized emails in one click.
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(smtp_ok: bool, manual_path: str) -> None:
    with st.sidebar:
        st.markdown("### Bulk Mail")
        st.caption("Solo local dashboard")
        st.divider()
        st.markdown("**How it works**")
        st.markdown(
            """
            1. Upload a CSV with **name** and **email**
            2. Review recipients and template
            3. Click **Send to all**
            4. Retry or download rejected rows
            """
        )
        st.divider()
        if smtp_ok:
            st.success("SMTP configured")
        else:
            st.error("SMTP not configured")
            st.caption("Copy `.env.example` to `.env` and add credentials.")
        st.divider()
        st.caption("📄 Project manual")
        st.code(manual_path, language=None)


def metric_cards(summary: dict[str, int]) -> None:
    specs = [
        ("total", "Total", "metric-total"),
        ("sent", "Sent", "metric-sent"),
        ("rejected", "Rejected", "metric-rejected"),
        ("pending", "Pending", "metric-pending"),
        ("need_again", "Need to send again", "metric-again"),
    ]
    cols = st.columns(5)
    for col, (key, label, css_class) in zip(cols, specs):
        value = summary.get(key, 0)
        col.markdown(
            f"""
            <div class="metric-card {css_class}">
              <div class="label">{label}</div>
              <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def empty_state_upload() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <div class="icon">📁</div>
          <h3>Upload a CSV to get started</h3>
          <p>Your file needs <strong>name</strong> and <strong>email</strong> columns.
          We'll validate addresses and show everyone before you send.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def success_banner(message: str) -> None:
    st.markdown(
        f'<div class="success-banner">✓ {message}</div>',
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str | None = None) -> None:
    st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def email_preview_html(html: str) -> None:
    st.markdown('<div class="email-preview-box"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.components.v1.html(html, height=320, scrolling=True)
