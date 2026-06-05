"""Send progress summary and recipient filtering."""

from __future__ import annotations

import pandas as pd

SENDABLE_STATUSES = {"pending", "rejected"}


def compute_summary(df: pd.DataFrame | None) -> dict[str, int]:
    if df is None or df.empty:
        return {
            "total": 0,
            "sent": 0,
            "rejected": 0,
            "pending": 0,
            "need_again": 0,
        }

    status = df["status"].astype(str).str.lower()
    sent = int((status == "sent").sum())
    rejected = int((status == "rejected").sum())
    pending = int((status == "pending").sum())
    total = sent + rejected + pending

    return {
        "total": total,
        "sent": sent,
        "rejected": rejected,
        "pending": pending,
        "need_again": pending + rejected,
    }


def get_rejected_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])
    return df[df["status"].astype(str).str.lower() == "rejected"].copy()


def get_sendable_indices(df: pd.DataFrame, only_rejected: bool = False) -> list[int]:
    if df is None or df.empty:
        return []
    status = df["status"].astype(str).str.lower()
    if only_rejected:
        mask = status == "rejected"
    else:
        mask = status.isin(SENDABLE_STATUSES)
    return df.index[mask].tolist()
