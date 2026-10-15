"""Customer-level RFM analytics foundation and explainable segmentation.

Implements leakage-safe qualifying purchase filtering at the invoice grain,
calculates Recency, Frequency, Tenure, and component-level Monetary values,
assigns deterministic scores and business segments, and tracks forward 90-day
repeat purchase targets across chronological evaluation cutoffs.
"""

from datetime import timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from retensight.config import PipelineConfig

logger = logging.getLogger(__name__)


def extract_qualifying_purchases(
    invoices_df: pd.DataFrame,
    as_of_date: pd.Timestamp,
) -> pd.DataFrame:
    """Filters invoice aggregates to qualifying customer merchandise purchase events

    strictly prior to or on `as_of_date`.

    A qualifying purchase event is defined as:
    1. A valid, non-null customer ID.
    2. Strictly on or before the snapshot cutoff (`invoice_date <= as_of_date`).
    3. Not a cancellation invoice (`is_cancellation == False` and invoice not starting with 'C').
    4. Not a bad-debt adjustment (`is_bad_debt == False` and invoice not starting with 'A').
    5. Contains positive standard product sales (`product_sales > 0.0`). Invoices
       containing solely shipping fees or administrative charges without merchandise
       are excluded.
    6. Total quantity is strictly positive (`total_quantity > 0`).

    Parameters
    ----------
    invoices_df : pd.DataFrame
        Invoice-grain aggregate DataFrame.
    as_of_date : pd.Timestamp
        Temporal snapshot cutoff.

    Returns
    -------
    pd.DataFrame
        Subset of invoices representing qualifying purchase events.
    """
    mask = (
        (invoices_df["invoice_date"] <= as_of_date)
        & invoices_df["has_customer_id"]
        & (~invoices_df["is_cancellation"])
        & (~invoices_df["is_bad_debt"])
        & (invoices_df["product_sales"] > 0.0)
        & (invoices_df["total_quantity"] > 0)
    )
    qualifying = invoices_df[mask].copy()
    logger.debug(
        "Extracted %d qualifying purchase invoices as of %s (across %d unique customers).",
        len(qualifying),
        as_of_date,
        qualifying["customer_id"].nunique(),
    )
    return qualifying


def get_frequency_score(frequency: int) -> int:
    """Assigns deterministic frequency score (1 to 5) with explicit retail binning

    to avoid arbitrary quantile collapse on F=1.

    Binning rationale:
    - F = 1 -> 1 (One-time buyer; ~28-33% of customer base)
    - F = 2 -> 2 (Repeat buyer / second order; ~16-19%)
    - F in [3, 4] -> 3 (Multi-order customer; ~19-21%)
    - F in [5, 8] -> 4 (Frequent loyal shopper; ~16-18%)
    - F >= 9 -> 5 (Highly frequent VIP; ~11-19%)
    """
    if frequency <= 1:
        return 1
    elif frequency == 2:
        return 2
    elif frequency in (3, 4):
        return 3
    elif 5 <= frequency <= 8:
        return 4
    else:
        return 5


def assign_crm_segment(row: pd.Series) -> str:
    """Assigns explainable CRM business segments from RFM scores and net spend.

    Segmentation Matrix (25 cells + Negative Spend):
    - Negative or Zero Spend: net_monetary_value <= 0
    - Champions: R in (4, 5) and F in (4, 5)
    - Potential Loyalists: R in (4, 5) and F in (2, 3)
    - New Customers: R in (4, 5) and F == 1
    - Loyal Customers: R == 3 and F in (3, 4, 5)
    - Promising: R == 3 and F in (1, 2)
    - Can't Lose Them: R in (1, 2) and F == 5
    - At Risk: R in (1, 2) and F in (3, 4)
    - About To Sleep: R == 2 and F in (1, 2)
    - Hibernating: R == 1 and F == 2
    - Lost: R == 1 and F == 1
    """
    if row["net_monetary_value"] <= 0:
        return "Negative or Zero Spend"

    r = int(row["r_score"])
    f = int(row["f_score"])

    if r in (4, 5) and f in (4, 5):
        return "Champions"
    elif r in (4, 5) and f in (2, 3):
        return "Potential Loyalists"
    elif r in (4, 5) and f == 1:
        return "New Customers"
    elif r == 3 and f in (3, 4, 5):
        return "Loyal Customers"
    elif r == 3 and f in (1, 2):
        return "Promising"
    elif r in (1, 2) and f == 5:
        return "Can't Lose Them"
    elif r in (1, 2) and f in (3, 4):
        return "At Risk"
    elif r == 2 and f in (1, 2):
        return "About To Sleep"
    elif r == 1 and f == 2:
        return "Hibernating"
    elif r == 1 and f == 1:
        return "Lost"
    else:
        return "Hibernating"


def compute_customer_rfm_snapshot(
    invoices_df: pd.DataFrame,
    snapshot_date: Union[str, pd.Timestamp],
    forward_target_days: Optional[int] = 90,
) -> pd.DataFrame:
    """Computes leakage-safe customer-level RFM features, component-level monetary

    breakdowns, tenure, scores, and forward target labels as of a specific cutoff.

    Parameters
    ----------
    invoices_df : pd.DataFrame
        Complete invoice aggregates DataFrame.
    snapshot_date : Union[str, pd.Timestamp]
        Historical cutoff timestamp (e.g. '2010-12-09 23:59:59').
    forward_target_days : Optional[int]
        Window in days following snapshot_date to observe forward repeat purchase
        behavior. If the window exceeds the maximum dataset invoice date, target
        is set to NA.

    Returns
    -------
    pd.DataFrame
        Customer-level RFM feature snapshot table.
    """
    ts = pd.to_datetime(snapshot_date)
    date_str = ts.strftime("%Y-%m-%d")
    logger.info("Computing customer RFM snapshot as of %s...", ts)

    # 1. Historical Invoices strictly up to snapshot cutoff
    hist_inv = invoices_df[invoices_df["invoice_date"] <= ts].copy()

    # 2. Extract qualifying purchase events
    qualifying_inv = extract_qualifying_purchases(invoices_df, as_of_date=ts)

    if len(qualifying_inv) == 0:
        raise ValueError(f"No qualifying purchase events found on or before {ts}.")

    # 3. Base customer aggregation on qualifying purchases
    cust_q = qualifying_inv.groupby("customer_id", sort=False).agg(
        first_purchase_date=("invoice_date", "min"),
        last_purchase_date=("invoice_date", "max"),
        frequency=("invoice", "nunique"),
        distinct_purchase_days=("invoice_date", lambda s: s.dt.date.nunique()),
        country=("country", lambda s: s.mode().iloc[0] if not s.empty else "Unspecified"),
        total_items_purchased=("total_quantity", "sum"),
    ).reset_index()

    # Derived recency and tenure in whole elapsed days
    cust_q["recency_days"] = (ts - cust_q["last_purchase_date"]).dt.total_seconds() / 86400.0
    cust_q["recency_days"] = cust_q["recency_days"].astype(int)

    cust_q["customer_tenure_days"] = (ts - cust_q["first_purchase_date"]).dt.total_seconds() / 86400.0
    cust_q["customer_tenure_days"] = cust_q["customer_tenure_days"].astype(int)

    # 4. Aggregate complete historical customer spend (sales, charges, cancellations)
    # Includes all commercial activity of the customer up to snapshot date
    cust_hist_all = hist_inv[hist_inv["has_customer_id"]].copy()
    spend_agg = cust_hist_all.groupby("customer_id", sort=False).agg(
        monetary_product_sales=("product_sales", "sum"),
        monetary_special_charges=("special_charges", "sum"),
        monetary_gross_sales=("gross_sales", "sum"),
        monetary_cancellations=("cancellation_value", "sum"),
        net_monetary_value=("net_value", "sum"),
        total_invoices_all=("invoice", "nunique"),
        cancellation_invoice_count=("is_cancellation", "sum"),
    ).reset_index()

    spend_agg["monetary_product_sales"] = spend_agg["monetary_product_sales"].round(2)
    spend_agg["monetary_special_charges"] = spend_agg["monetary_special_charges"].round(2)
    spend_agg["monetary_gross_sales"] = spend_agg["monetary_gross_sales"].round(2)
    spend_agg["monetary_cancellations"] = spend_agg["monetary_cancellations"].round(2)
    spend_agg["net_monetary_value"] = spend_agg["net_monetary_value"].round(2)

    # 5. Merge qualifying activity with spend components
    rfm_df = cust_q.merge(spend_agg, on="customer_id", how="left")

    # Average order value across qualifying purchase frequency
    rfm_df["avg_order_value"] = np.where(
        rfm_df["net_monetary_value"] > 0,
        (rfm_df["net_monetary_value"] / rfm_df["frequency"]).round(2),
        0.0,
    )

    # 6. RFM Scoring
    # R Score: lower recency_days = higher engagement (5 = best, 1 = worst)
    # Use quantile ranking with deterministic rank method
    r_pct = rfm_df["recency_days"].rank(method="first", ascending=True, pct=True)
    rfm_df["r_score"] = pd.cut(
        r_pct,
        bins=[-np.inf, 0.20, 0.40, 0.60, 0.80, np.inf],
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    # F Score: deterministic retail binning
    rfm_df["f_score"] = rfm_df["frequency"].apply(get_frequency_score)

    # M Score: positive spend quintiles (1 to 5), 0 for negative/zero spend
    rfm_df["m_score"] = 0
    pos_mask = rfm_df["net_monetary_value"] > 0
    if pos_mask.any():
        m_pct = rfm_df.loc[pos_mask, "net_monetary_value"].rank(method="first", ascending=True, pct=True)
        rfm_df.loc[pos_mask, "m_score"] = pd.cut(
            m_pct,
            bins=[-np.inf, 0.20, 0.40, 0.60, 0.80, np.inf],
            labels=[1, 2, 3, 4, 5],
        ).astype(int)

    rfm_df["rfm_score"] = (
        rfm_df["r_score"].astype(str)
        + rfm_df["f_score"].astype(str)
        + rfm_df["m_score"].astype(str)
    )

    # 7. Business Segment Assignment
    rfm_df["segment"] = rfm_df.apply(assign_crm_segment, axis=1)

    # 8. Forward 90-day Target Labeling
    # Forward window: (snapshot_date, snapshot_date + forward_target_days]
    dataset_max_date = invoices_df["invoice_date"].max()
    if forward_target_days is not None:
        forward_end = ts + timedelta(days=forward_target_days)
        is_fully_observed = forward_end <= dataset_max_date

        if is_fully_observed:
            future_mask = (
                (invoices_df["invoice_date"] > ts)
                & (invoices_df["invoice_date"] <= forward_end)
                & invoices_df["has_customer_id"]
                & (~invoices_df["is_cancellation"])
                & (~invoices_df["is_bad_debt"])
                & (invoices_df["product_sales"] > 0.0)
                & (invoices_df["total_quantity"] > 0)
            )
            future_qualifying = invoices_df[future_mask]
            repeat_cust_ids = set(future_qualifying["customer_id"].unique())

            # Future spend in window
            future_spend_mask = (
                (invoices_df["invoice_date"] > ts)
                & (invoices_df["invoice_date"] <= forward_end)
                & invoices_df["has_customer_id"]
            )
            future_spend = (
                invoices_df[future_spend_mask]
                .groupby("customer_id")["net_value"]
                .sum()
                .round(2)
                .to_dict()
            )

            rfm_df["target_repeat_purchase_90d"] = rfm_df["customer_id"].isin(repeat_cust_ids).astype(int)
            rfm_df["target_spend_90d"] = rfm_df["customer_id"].map(future_spend).fillna(0.0).round(2)
            rfm_df["is_target_window_observed"] = True
            logger.info(
                "Forward 90-day target computed: %d / %d (%.1f%%) repeated in [%s to %s].",
                rfm_df["target_repeat_purchase_90d"].sum(),
                len(rfm_df),
                100.0 * rfm_df["target_repeat_purchase_90d"].mean(),
                ts.strftime("%Y-%m-%d"),
                forward_end.strftime("%Y-%m-%d"),
            )
        else:
            rfm_df["target_repeat_purchase_90d"] = pd.Series([None] * len(rfm_df), dtype="Int64")
            rfm_df["target_spend_90d"] = pd.Series([None] * len(rfm_df), dtype="Float64")
            rfm_df["is_target_window_observed"] = False
            logger.info(
                "Forward 90-day target window [%s to %s] unobserved (dataset ends at %s).",
                ts.strftime("%Y-%m-%d"),
                forward_end.strftime("%Y-%m-%d"),
                dataset_max_date.strftime("%Y-%m-%d"),
            )
    else:
        rfm_df["target_repeat_purchase_90d"] = pd.Series([None] * len(rfm_df), dtype="Int64")
        rfm_df["target_spend_90d"] = pd.Series([None] * len(rfm_df), dtype="Float64")
        rfm_df["is_target_window_observed"] = False

    rfm_df["snapshot_date"] = date_str

    # 9. Invariants and Integrity Assertions
    assert len(rfm_df) == rfm_df["customer_id"].nunique(), "Primary key violation: Duplicate customer IDs."
    assert (rfm_df["recency_days"] >= 0).all(), "Invariant violation: Negative recency found."
    assert (rfm_df["customer_tenure_days"] >= rfm_df["recency_days"]).all(), (
        "Invariant violation: Tenure cannot be strictly less than recency."
    )
    assert (rfm_df["frequency"] >= 1).all(), "Invariant violation: Frequency must be >= 1 for qualifying customers."
    assert (rfm_df["distinct_purchase_days"] <= rfm_df["frequency"]).all(), (
        "Invariant violation: Distinct purchase days cannot exceed total qualifying invoices."
    )
    assert rfm_df["r_score"].isin([1, 2, 3, 4, 5]).all(), "R-score out of bounds [1..5]."
    assert rfm_df["f_score"].isin([1, 2, 3, 4, 5]).all(), "F-score out of bounds [1..5]."
    assert rfm_df["m_score"].isin([0, 1, 2, 3, 4, 5]).all(), "M-score out of bounds [0..5]."
    assert rfm_df["segment"].notna().all(), "Unassigned segment found."

    # Column ordering for clear tabular display and modeling
    ordered_cols = [
        "customer_id",
        "snapshot_date",
        "country",
        "first_purchase_date",
        "last_purchase_date",
        "recency_days",
        "customer_tenure_days",
        "frequency",
        "distinct_purchase_days",
        "total_items_purchased",
        "monetary_product_sales",
        "monetary_special_charges",
        "monetary_gross_sales",
        "monetary_cancellations",
        "net_monetary_value",
        "avg_order_value",
        "r_score",
        "f_score",
        "m_score",
        "rfm_score",
        "segment",
        "is_target_window_observed",
        "target_repeat_purchase_90d",
        "target_spend_90d",
    ]
    rfm_df = rfm_df[ordered_cols].sort_values("customer_id").reset_index(drop=True)

    logger.info(
        "Successfully constructed RFM snapshot for %s: %d eligible customers, %d segments.",
        date_str,
        len(rfm_df),
        rfm_df["segment"].nunique(),
    )
    return rfm_df


def build_all_rfm_snapshots(
    invoices_df: pd.DataFrame,
    evaluation_cutoffs: Sequence[str] = PipelineConfig.evaluation_cutoffs,
    full_history_cutoff: str = PipelineConfig.full_history_cutoff,
    forward_target_days: int = PipelineConfig.forward_target_window_days,
) -> Dict[str, pd.DataFrame]:
    """Generates RFM snapshots for all evaluation cutoffs and the full dataset end.

    Parameters
    ----------
    invoices_df : pd.DataFrame
        Complete invoice aggregates DataFrame.
    evaluation_cutoffs : Sequence[str]
        Chronological evaluation cutoff timestamp strings.
    full_history_cutoff : str
        Dataset end timestamp string.
    forward_target_days : int
        Target window duration in days.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary mapping cutoff label to RFM snapshot DataFrame.
    """
    all_cutoffs = list(evaluation_cutoffs) + [full_history_cutoff]
    snapshots: Dict[str, pd.DataFrame] = {}

    for cutoff_str in all_cutoffs:
        ts = pd.to_datetime(cutoff_str)
        date_label = ts.strftime("%Y-%m-%d")
        snapshot_df = compute_customer_rfm_snapshot(
            invoices_df=invoices_df,
            snapshot_date=ts,
            forward_target_days=forward_target_days,
        )
        snapshots[date_label] = snapshot_df

    return snapshots


def summarize_rfm_snapshots(
    snapshots: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """Summarizes customer counts, repeat purchase rates, monetary totals,

    and segment distributions across evaluation cutoffs.
    """
    summary: Dict[str, Any] = {
        "cutoffs": {},
        "segment_distribution_cross_cutoff": {},
    }

    all_segments = [
        "Champions",
        "Loyal Customers",
        "Potential Loyalists",
        "New Customers",
        "Promising",
        "About To Sleep",
        "At Risk",
        "Can't Lose Them",
        "Hibernating",
        "Lost",
        "Negative or Zero Spend",
    ]

    for date_label, df in snapshots.items():
        n_cust = len(df)
        has_target = bool(df["is_target_window_observed"].iloc[0])
        repeat_rate = (
            float(round(df["target_repeat_purchase_90d"].mean() * 100.0, 2))
            if has_target
            else None
        )
        repeat_count = (
            int(df["target_repeat_purchase_90d"].sum()) if has_target else None
        )

        cutoff_meta = {
            "snapshot_date": date_label,
            "eligible_customers": n_cust,
            "mean_recency_days": float(round(df["recency_days"].mean(), 1)),
            "median_recency_days": float(round(df["recency_days"].median(), 1)),
            "mean_frequency": float(round(df["frequency"].mean(), 2)),
            "median_frequency": float(round(df["frequency"].median(), 1)),
            "mean_net_monetary_gbp": float(round(df["net_monetary_value"].mean(), 2)),
            "total_net_monetary_gbp": float(round(df["net_monetary_value"].sum(), 2)),
            "is_target_window_observed": has_target,
            "repeat_purchasers_90d": repeat_count,
            "repeat_purchase_rate_pct": repeat_rate,
            "segment_counts": df["segment"].value_counts().to_dict(),
        }
        summary["cutoffs"][date_label] = cutoff_meta

    # Cross-cutoff segment percentages
    for seg in all_segments:
        summary["segment_distribution_cross_cutoff"][seg] = {}
        for date_label, df in snapshots.items():
            cnt = int((df["segment"] == seg).sum())
            pct = float(round((cnt / len(df)) * 100.0, 2))
            summary["segment_distribution_cross_cutoff"][seg][date_label] = {
                "count": cnt,
                "pct": pct,
            }

    return summary


def save_rfm_summary_reports(
    summary_dict: Dict[str, Any],
    json_path: Path = Path("reports/rfm_segmentation_summary.json"),
    md_path: Path = Path("reports/rfm_segmentation_summary.md"),
) -> None:
    """Exports RFM summary to structured JSON and human-readable Markdown."""
    json_path = Path(json_path)
    md_path = Path(md_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)
    logger.info("Saved RFM segmentation summary JSON to '%s'.", json_path)

    cutoffs = summary_dict["cutoffs"]
    seg_cross = summary_dict["segment_distribution_cross_cutoff"]
    cutoff_dates = list(cutoffs.keys())

    md_lines = [
        "# RetenSight — Customer RFM Analytics & Segmentation Summary",
        "",
        "## Executive Summary",
        "",
        "This report details the customer-level RFM features, deterministic scoring, explainable CRM segmentation, ",
        "and forward 90-day repeat-purchase rates across chronological evaluation cutoffs for the UCI Online Retail II dataset.",
        "",
        "## Cutoff Overview & Forward 90-Day Target Calibration",
        "",
        "| Evaluation Cutoff | Eligible Customers | Mean Recency (Days) | Mean Frequency | Total Net Spend (£) | 90-Day Repeat Buyers | Repeat Purchase Rate (%) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for d, info in cutoffs.items():
        rep_cnt = f"{info['repeat_purchasers_90d']:,}" if info["repeat_purchasers_90d"] is not None else "N/A"
        rep_rate = f"{info['repeat_purchase_rate_pct']:.1f}%" if info["repeat_purchase_rate_pct"] is not None else "Unobserved (Dataset End)"
        md_lines.append(
            f"| `{d}` | {info['eligible_customers']:,} | {info['mean_recency_days']:.1f} | "
            f"{info['mean_frequency']:.2f} | £{info['total_net_monetary_gbp']:,.2f} | "
            f"{rep_cnt} | {rep_rate} |"
        )

    md_lines.extend([
        "",
        "## Cross-Cutoff CRM Segment Distribution",
        "",
        f"| CRM Segment | {' | '.join([f'`{d}` Count (%)' for d in cutoff_dates])} |",
        f"| :--- | {' | '.join(['---:'] * len(cutoff_dates))} |",
    ])

    for seg, d_dict in seg_cross.items():
        vals = [f"{d_dict[d]['count']:,} ({d_dict[d]['pct']:.1f}%)" for d in cutoff_dates]
        md_lines.append(f"| **{seg}** | {' | '.join(vals)} |")

    md_lines.extend([
        "",
        "## Segmentation Methodology & Rules",
        "",
        "1. **Qualifying Purchase Events:** Only invoices with confirmed positive product sales (`product_sales > 0`), strictly positive quantities, valid customer IDs, and non-cancellation status increment purchase frequency. Charge-only invoices (postage, bank fees) do not count as purchases.",
        "2. **Multi-line Invoice Aggregation:** Aggregation is performed at the unique invoice ID grain. Multi-line orders never inflate purchase frequency.",
        "3. **Same-Day Order Handling:** Each distinct invoice represents a separate customer order transaction (`frequency`). Daily cadence is tracked independently via `distinct_purchase_days`.",
        "4. **Deterministic Frequency Scoring:** Discrete binning ensures that all 1-time buyers receive score 1, 2-order buyers score 2, 3-4 orders score 3, 5-8 orders score 4, and 9+ orders score 5, completely eliminating arbitrary tie-breaking.",
        "5. **Negative Net Spend Isolation:** Customers with net cumulative spend <= £0.00 due to returns are segregated into a dedicated `Negative or Zero Spend` segment.",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    logger.info("Saved RFM segmentation summary Markdown to '%s'.", md_path)
