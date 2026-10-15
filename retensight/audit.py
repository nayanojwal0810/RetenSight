"""Data quality auditing, invariant checking, and reconciliation reports."""

from dataclasses import asdict
import json
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from retensight.deduplication import DeduplicationAudit

logger = logging.getLogger(__name__)


def generate_pipeline_audit(
    dedup_audit: DeduplicationAudit,
    transactions_df: pd.DataFrame,
    invoices_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Computes comprehensive audit statistics and checks reconciliation invariants.

    Parameters
    ----------
    dedup_audit : DeduplicationAudit
        Audit object from cross-sheet deduplication.
    transactions_df : pd.DataFrame
        Cleaned transactions DataFrame.
    invoices_df : pd.DataFrame
        Aggregated invoices DataFrame.

    Returns
    -------
    Dict[str, Any]
        Structured audit dictionary.
    """
    logger.info("Computing pipeline audit metrics and reconciliation invariants...")

    # Financial sums from transactions
    tx_line_value_sum = float(transactions_df["line_total"].sum())
    tx_gross_sales = float(
        transactions_df[transactions_df["transaction_category"] == "standard_sale"]["line_total"].sum()
    )
    tx_cancellations = float(
        transactions_df[transactions_df["transaction_category"] == "cancellation"]["line_total"].sum()
    )
    tx_bad_debt = float(
        transactions_df[transactions_df["transaction_category"] == "bad_debt_adjustment"]["line_total"].sum()
    )

    # Attribution breakdown
    attr_tx = transactions_df[transactions_df["has_customer_id"]]
    unattr_tx = transactions_df[~transactions_df["has_customer_id"]]

    attr_gross_sales = float(
        attr_tx[attr_tx["transaction_category"] == "standard_sale"]["line_total"].sum()
    )
    unattr_gross_sales = float(
        unattr_tx[unattr_tx["transaction_category"] == "standard_sale"]["line_total"].sum()
    )

    attr_cancellations = float(
        attr_tx[attr_tx["transaction_category"] == "cancellation"]["line_total"].sum()
    )
    unattr_cancellations = float(
        unattr_tx[unattr_tx["transaction_category"] == "cancellation"]["line_total"].sum()
    )

    # Invoices metrics
    inv_net_value_sum = float(invoices_df["net_value"].sum())
    inv_gross_sales_sum = float(invoices_df["gross_sales"].sum())
    inv_cancellation_sum = float(invoices_df["cancellation_value"].sum())

    distinct_customers = int(transactions_df["customer_id"].nunique(dropna=True))
    total_invoices = len(invoices_df)
    customer_invoices = int(invoices_df["has_customer_id"].sum())
    unattributed_invoices = total_invoices - customer_invoices

    # Invariant verification
    invariants = {
        "raw_minus_duplicates_equals_retained": (
            dedup_audit.total_raw_rows - dedup_audit.cross_sheet_duplicates_removed
            == len(transactions_df)
        ),
        "transaction_lines_equal_invoice_line_count_sum": (
            len(transactions_df) == int(invoices_df["line_count"].sum())
        ),
        "transaction_quantities_equal_invoice_quantities": (
            int(transactions_df["quantity"].sum()) == int(invoices_df["total_quantity"].sum())
        ),
        "transaction_net_value_equals_invoice_net_value": bool(
            np.isclose(tx_line_value_sum, inv_net_value_sum, atol=1.0)
        ),
        "gross_plus_returns_plus_bad_debt_equals_total_value": bool(
            np.isclose(
                tx_gross_sales + tx_cancellations + tx_bad_debt,
                tx_line_value_sum,
                atol=1.0,
            )
        ),
    }

    # Verify all invariants hold
    for inv_name, passed in invariants.items():
        if not passed:
            raise ValueError(f"CRITICAL RECONCILIATION INVARIANT FAILED: {inv_name}")

    audit_data = {
        "ingestion": {
            "sheet1_name": dedup_audit.sheet1_name,
            "sheet1_raw_rows": dedup_audit.sheet1_rows_read,
            "sheet2_name": dedup_audit.sheet2_name,
            "sheet2_raw_rows": dedup_audit.sheet2_rows_read,
            "total_raw_rows_ingested": dedup_audit.total_raw_rows,
        },
        "deduplication": {
            "cross_sheet_duplicates_removed": dedup_audit.cross_sheet_duplicates_removed,
            "retained_rows_post_deduplication": dedup_audit.retained_rows,
            "sheet1_rows_in_same_sheet_duplicates": dedup_audit.sheet1_rows_in_same_sheet_dups,
            "sheet2_rows_in_same_sheet_duplicates_pre": dedup_audit.sheet2_rows_in_same_sheet_dups_pre,
            "overlap_window_start": dedup_audit.overlap_window_start,
            "overlap_window_end": dedup_audit.overlap_window_end,
            "same_sheet_duplicates_preserved": True,
        },
        "transactions_breakdown": {
            "total_retained_transactions": len(transactions_df),
            "customer_attributed_transactions": len(attr_tx),
            "unattributed_transactions": len(unattr_tx),
            "standard_sales_count": int((transactions_df["transaction_category"] == "standard_sale").sum()),
            "cancellations_count": int((transactions_df["transaction_category"] == "cancellation").sum()),
            "bad_debt_adjustments_count": int(
                (transactions_df["transaction_category"] == "bad_debt_adjustment").sum()
            ),
            "inventory_adjustments_count": int(
                (transactions_df["transaction_category"] == "inventory_adjustment").sum()
            ),
            "promotional_freebies_count": int(
                (transactions_df["transaction_category"] == "promotional_freebie").sum()
            ),
            "zero_price_rows_count": int(transactions_df["is_zero_price"].sum()),
            "negative_price_rows_count": int(transactions_df["is_negative_price"].sum()),
        },
        "invoice_breakdown": {
            "total_unique_invoices": total_invoices,
            "customer_invoices": customer_invoices,
            "unattributed_invoices": unattributed_invoices,
            "customer_sales_invoices": int((invoices_df["invoice_type"] == "customer_sale").sum()),
            "customer_cancellation_invoices": int(
                (invoices_df["invoice_type"] == "customer_cancellation").sum()
            ),
            "unattributed_sales_invoices": int(
                (invoices_df["invoice_type"] == "unattributed_sale").sum()
            ),
            "unattributed_cancellation_invoices": int(
                (invoices_df["invoice_type"] == "unattributed_cancellation").sum()
            ),
            "inventory_adjustment_invoices": int(
                (invoices_df["invoice_type"] == "inventory_adjustment").sum()
            ),
            "bad_debt_adjustment_invoices": int(
                (invoices_df["invoice_type"] == "bad_debt_adjustment").sum()
            ),
            "distinct_valid_customers": distinct_customers,
        },
        "financial_reconciliation": {
            "gross_positive_sales_gbp": round(tx_gross_sales, 2),
            "attributed_gross_sales_gbp": round(attr_gross_sales, 2),
            "unattributed_gross_sales_gbp": round(unattr_gross_sales, 2),
            "cancellations_value_gbp": round(tx_cancellations, 2),
            "attributed_cancellations_gbp": round(attr_cancellations, 2),
            "unattributed_cancellations_gbp": round(unattr_cancellations, 2),
            "bad_debt_adjustments_gbp": round(tx_bad_debt, 2),
            "net_commercial_revenue_gbp": round(tx_line_value_sum, 2),
            "invoice_net_revenue_sum_gbp": round(inv_net_value_sum, 2),
            "revenue_discrepancy_gbp": round(abs(tx_line_value_sum - inv_net_value_sum), 4),
        },
        "reconciliation_invariants": invariants,
    }

    return audit_data


def save_audit_reports(
    audit_dict: Dict[str, Any],
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Exports machine-readable JSON and human-readable Markdown audit summaries."""
    json_path = Path(json_path)
    markdown_path = Path(markdown_path)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_dict, f, indent=2)
    logger.info("Saved machine-readable audit to: %s", json_path)

    # 2. Format and save Markdown
    md_content = generate_markdown_report(audit_dict)
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Saved human-readable cleaning summary to: %s", markdown_path)


def format_gbp(val: float) -> str:
    """Formats numeric value as GBP string with clean negative sign handling."""
    if val < 0:
        return f"-£{abs(val):,.2f}"
    return f"£{val:,.2f}"


def generate_markdown_report(audit: Dict[str, Any]) -> str:
    """Renders human-readable markdown summary report from audit data."""
    ing = audit["ingestion"]
    dedup = audit["deduplication"]
    tx = audit["transactions_breakdown"]
    inv = audit["invoice_breakdown"]
    fin = audit["financial_reconciliation"]
    invariants = audit["reconciliation_invariants"]

    lines = [
        "# RetenSight — Data Cleaning and Reconciliation Audit Report",
        "",
        "## 1. Executive Summary",
        "",
        "- **Raw Rows Ingested**: {:,} across 2 workbook sheets (`{}`: {:,}, `{}`: {:,})".format(
            ing["total_raw_rows_ingested"],
            ing["sheet1_name"],
            ing["sheet1_raw_rows"],
            ing["sheet2_name"],
            ing["sheet2_raw_rows"],
        ),
        "- **Exact Cross-Sheet Duplicates Removed**: {:,} (from `{}` overlap)".format(
            dedup["cross_sheet_duplicates_removed"], ing["sheet2_name"]
        ),
        "- **Retained Transactions**: {:,}".format(dedup["retained_rows_post_deduplication"]),
        "- **Distinct Valid Customers**: {:,}".format(inv["distinct_valid_customers"]),
        "- **Total Unique Invoices**: {:,}".format(inv["total_unique_invoices"]),
        "- **Gross Commercial Sales**: {}".format(format_gbp(fin["gross_positive_sales_gbp"])),
        "- **Cancellations / Refunds**: {}".format(format_gbp(fin["cancellations_value_gbp"])),
        "- **Bad Debt Adjustments**: {}".format(format_gbp(fin["bad_debt_adjustments_gbp"])),
        "- **Net Commercial Revenue**: {}".format(format_gbp(fin["net_commercial_revenue_gbp"])),
        "",
        "---",
        "",
        "## 2. Ingestion & Duplicate Resolution",
        "",
        "| Metric | Value | Notes |",
        "| :--- | :--- | :--- |",
        "| Sheet 1 Raw Rows (`{}`) | {:,} | Dates: 2009-12-01 to 2010-12-09 |".format(
            ing["sheet1_name"], ing["sheet1_raw_rows"]
        ),
        "| Sheet 2 Raw Rows (`{}`) | {:,} | Dates: 2010-12-01 to 2011-12-09 |".format(
            ing["sheet2_name"], ing["sheet2_raw_rows"]
        ),
        "| Date Overlap Window | {} to {} | Overlap period |".format(
            dedup["overlap_window_start"], dedup["overlap_window_end"]
        ),
        "| Cross-Sheet 1-to-1 Duplicates Removed | {:,} | Removed strictly from `{}` |".format(
            dedup["cross_sheet_duplicates_removed"], ing["sheet2_name"]
        ),
        "| Sheet 1 Same-Sheet Duplicates Preserved | {:,} | Legitimate repeat rows kept |".format(
            dedup["sheet1_rows_in_same_sheet_duplicates"]
        ),
        "| Retained Rows Post-Deduplication | {:,} | Exactly Sheet 1 + Retained Sheet 2 |".format(
            dedup["retained_rows_post_deduplication"]
        ),
        "",
        "---",
        "",
        "## 3. Transaction Breakdown by Classification",
        "",
        "| Category | Rows | % of Total | Description |",
        "| :--- | :--- | :--- | :--- |",
        "| `standard_sale` | {:,} | {:.2f}% | Commercial positive sales (qty > 0, price > 0) |".format(
            tx["standard_sales_count"],
            (tx["standard_sales_count"] / tx["total_retained_transactions"]) * 100,
        ),
        "| `cancellation` | {:,} | {:.2f}% | Invoices starting with 'C' (returns/cancellations) |".format(
            tx["cancellations_count"],
            (tx["cancellations_count"] / tx["total_retained_transactions"]) * 100,
        ),
        "| `inventory_adjustment` | {:,} | {:.2f}% | Administrative loss/found write-offs (price=0, no customer ID) |".format(
            tx["inventory_adjustments_count"],
            (tx["inventory_adjustments_count"] / tx["total_retained_transactions"]) * 100,
        ),
        "| `promotional_freebie` | {:,} | {:.2f}% | Free gifts with customer orders (price=0, customer ID present) |".format(
            tx["promotional_freebies_count"],
            (tx["promotional_freebies_count"] / tx["total_retained_transactions"]) * 100,
        ),
        "| `bad_debt_adjustment` | {:,} | {:.4f}% | Invoices starting with 'A' (accounting debt write-offs) |".format(
            tx["bad_debt_adjustments_count"],
            (tx["bad_debt_adjustments_count"] / tx["total_retained_transactions"]) * 100,
        ),
        "| **Total Retained Rows** | **{:,}** | **100.00%** | |".format(tx["total_retained_transactions"]),
        "",
        "### Customer Attribution",
        "- **Customer-Attributed Transactions**: {:,} ({:.2f}%)".format(
            tx["customer_attributed_transactions"],
            (tx["customer_attributed_transactions"] / tx["total_retained_transactions"]) * 100,
        ),
        "- **Unattributed Transactions**: {:,} ({:.2f}%)".format(
            tx["unattributed_transactions"],
            (tx["unattributed_transactions"] / tx["total_retained_transactions"]) * 100,
        ),
        "",
        "---",
        "",
        "## 4. Invoice Aggregation",
        "",
        "| Invoice Type | Invoices | Line Count | Distinct Customers |",
        "| :--- | :--- | :--- | :--- |",
        "| Customer Sales (`customer_sale`) | {:,} | Attributed | {:,} |".format(
            inv["customer_sales_invoices"], inv["distinct_valid_customers"]
        ),
        "| Customer Cancellations (`customer_cancellation`) | {:,} | Attributed | - |".format(
            inv["customer_cancellation_invoices"]
        ),
        "| Unattributed Sales (`unattributed_sale`) | {:,} | Guest checkout | N/A |".format(
            inv["unattributed_sales_invoices"]
        ),
        "| Unattributed Cancellations | {:,} | Guest returns | N/A |".format(
            inv["unattributed_cancellation_invoices"]
        ),
        "| Inventory Adjustments | {:,} | Internal warehouse | N/A |".format(
            inv["inventory_adjustment_invoices"]
        ),
        "| Bad Debt Adjustments | {:,} | Accounting adjustments | N/A |".format(
            inv["bad_debt_adjustment_invoices"]
        ),
        "| **Total Unique Invoices** | **{:,}** | **100% Accounted** | |".format(
            inv["total_unique_invoices"]
        ),
        "",
        "---",
        "",
        "## 5. Financial Reconciliation",
        "",
        "| Revenue Stream | Attributed | Unattributed | Total |",
        "| :--- | :--- | :--- | :--- |",
        "| **Gross Sales** | {} | {} | {} |".format(
            format_gbp(fin["attributed_gross_sales_gbp"]),
            format_gbp(fin["unattributed_gross_sales_gbp"]),
            format_gbp(fin["gross_positive_sales_gbp"]),
        ),
        "| **Cancellations / Refunds** | {} | {} | {} |".format(
            format_gbp(fin["attributed_cancellations_gbp"]),
            format_gbp(fin["unattributed_cancellations_gbp"]),
            format_gbp(fin["cancellations_value_gbp"]),
        ),
        "| **Bad Debt Adjustments** | {} | {} | {} |".format(
            format_gbp(0.0),
            format_gbp(fin["bad_debt_adjustments_gbp"]),
            format_gbp(fin["bad_debt_adjustments_gbp"]),
        ),
        "| **Net Revenue** | **{}** | **{}** | **{}** |".format(
            format_gbp(fin["attributed_gross_sales_gbp"] + fin["attributed_cancellations_gbp"]),
            format_gbp(fin["unattributed_gross_sales_gbp"]
            + fin["unattributed_cancellations_gbp"]
            + fin["bad_debt_adjustments_gbp"]),
            format_gbp(fin["net_commercial_revenue_gbp"]),
        ),

        "",
        "---",
        "",
        "## 6. Mathematical Invariants Verification",
        "",
    ]

    for inv_name, status in invariants.items():
        status_icon = "PASSED [✓]" if status else "FAILED [X]"
        lines.append(f"- **{inv_name}**: {status_icon}")

    lines.append("")
    return "\n".join(lines)
