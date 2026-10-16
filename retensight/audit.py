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

    # Financial sums by transaction category
    tx_prod_sales = float(
        transactions_df[transactions_df["transaction_category"] == "standard_product_sale"][
            "line_total"
        ].sum()
    )
    tx_spec_charges = float(
        transactions_df[transactions_df["transaction_category"] == "special_commercial_charge"][
            "line_total"
        ].sum()
    )
    tx_gross_sales = float(tx_prod_sales + tx_spec_charges)
    tx_cancellations = float(
        transactions_df[transactions_df["transaction_category"] == "cancellation"]["line_total"].sum()
    )
    tx_bad_debt = float(
        transactions_df[transactions_df["transaction_category"] == "bad_debt_adjustment"][
            "line_total"
        ].sum()
    )
    tx_all_net_value = float(transactions_df["line_total"].sum())
    tx_net_commercial_value = float(tx_gross_sales + tx_cancellations)

    # Attribution breakdown
    attr_tx = transactions_df[transactions_df["has_customer_id"]]
    unattr_tx = transactions_df[~transactions_df["has_customer_id"]]

    attr_prod_sales = float(
        attr_tx[attr_tx["transaction_category"] == "standard_product_sale"]["line_total"].sum()
    )
    unattr_prod_sales = float(
        unattr_tx[unattr_tx["transaction_category"] == "standard_product_sale"]["line_total"].sum()
    )

    attr_spec_charges = float(
        attr_tx[attr_tx["transaction_category"] == "special_commercial_charge"]["line_total"].sum()
    )
    unattr_spec_charges = float(
        unattr_tx[unattr_tx["transaction_category"] == "special_commercial_charge"]["line_total"].sum()
    )

    attr_cancellations = float(
        attr_tx[attr_tx["transaction_category"] == "cancellation"]["line_total"].sum()
    )
    unattr_cancellations = float(
        unattr_tx[unattr_tx["transaction_category"] == "cancellation"]["line_total"].sum()
    )

    # Invoices metrics
    inv_prod_sales_sum = float(invoices_df["product_sales"].sum())
    inv_spec_charges_sum = float(invoices_df["special_charges"].sum())
    inv_gross_sales_sum = float(invoices_df["gross_sales"].sum())
    inv_cancellation_sum = float(invoices_df["cancellation_value"].sum())
    inv_bad_debt_sum = float(invoices_df["bad_debt_value"].sum())
    inv_net_value_sum = float(invoices_df["net_value"].sum())

    distinct_customers = int(transactions_df["customer_id"].nunique(dropna=True))
    total_invoices = len(invoices_df)
    customer_invoices = int(invoices_df["has_customer_id"].sum())
    unattributed_invoices = total_invoices - customer_invoices

    # Customer commercial / model-ready vs attributed
    customer_commercial_ready_count = int(transactions_df["is_commercial_customer_ready"].sum())
    customer_attributed_count = int(transactions_df["has_customer_id"].sum())
    promotional_freebies_count = int((transactions_df["transaction_category"] == "promotional_freebie").sum())

    # Component-level invariant verification (penny tolerance 0.01)
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
        "product_sales_reconciliation": bool(
            np.isclose(tx_prod_sales, inv_prod_sales_sum, atol=0.01)
        ),
        "special_charges_reconciliation": bool(
            np.isclose(tx_spec_charges, inv_spec_charges_sum, atol=0.01)
        ),
        "cancellation_value_reconciliation": bool(
            np.isclose(tx_cancellations, inv_cancellation_sum, atol=0.01)
        ),
        "bad_debt_value_reconciliation": bool(
            np.isclose(tx_bad_debt, inv_bad_debt_sum, atol=0.01)
        ),
        "all_transactions_net_value_equals_invoice_net_value": bool(
            np.isclose(tx_all_net_value, inv_net_value_sum, atol=0.01)
        ),
        "commercial_net_plus_bad_debt_equals_all_net": bool(
            np.isclose(tx_net_commercial_value + tx_bad_debt, tx_all_net_value, atol=0.01)
        ),
        "customer_commercial_ready_count_invariant": (
            customer_commercial_ready_count == customer_attributed_count - promotional_freebies_count
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
            "customer_attributed_transactions": customer_attributed_count,
            "customer_commercial_ready_transactions": customer_commercial_ready_count,
            "unattributed_transactions": len(unattr_tx),
            "standard_product_sales_count": int(
                (transactions_df["transaction_category"] == "standard_product_sale").sum()
            ),
            "special_commercial_charges_count": int(
                (transactions_df["transaction_category"] == "special_commercial_charge").sum()
            ),
            "cancellations_count": int((transactions_df["transaction_category"] == "cancellation").sum()),
            "bad_debt_adjustments_count": int(
                (transactions_df["transaction_category"] == "bad_debt_adjustment").sum()
            ),
            "inventory_adjustments_count": int(
                (transactions_df["transaction_category"] == "inventory_adjustment").sum()
            ),
            "promotional_freebies_count": promotional_freebies_count,
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
            "invoices_with_positive_cancellation_lines": int(
                invoices_df["has_positive_cancellation_line"].sum()
            ),
        },
        "financial_reconciliation": {
            "gross_product_sales_gbp": round(tx_prod_sales, 2),
            "attributed_product_sales_gbp": round(attr_prod_sales, 2),
            "unattributed_product_sales_gbp": round(unattr_prod_sales, 2),
            "special_commercial_charges_gbp": round(tx_spec_charges, 2),
            "attributed_special_charges_gbp": round(attr_spec_charges, 2),
            "unattributed_special_charges_gbp": round(unattr_spec_charges, 2),
            "gross_sales_gbp": round(tx_gross_sales, 2),
            "cancellations_value_gbp": round(tx_cancellations, 2),
            "attributed_cancellations_gbp": round(attr_cancellations, 2),
            "unattributed_cancellations_gbp": round(unattr_cancellations, 2),
            "net_commercial_value_gbp": round(tx_net_commercial_value, 2),
            "bad_debt_adjustments_gbp": round(tx_bad_debt, 2),
            "all_transactions_net_value_gbp": round(tx_all_net_value, 2),
            "invoice_net_revenue_sum_gbp": round(inv_net_value_sum, 2),
            "revenue_discrepancy_gbp": round(abs(tx_all_net_value - inv_net_value_sum), 4),
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
    """Render a concise cleaning and reconciliation summary from the audit data."""
    ing = audit["ingestion"]
    dedup = audit["deduplication"]
    tx = audit["transactions_breakdown"]
    inv = audit["invoice_breakdown"]
    fin = audit["financial_reconciliation"]
    invariants = audit["reconciliation_invariants"]

    rows = [
        ("Rows ingested", f"{ing['total_raw_rows_ingested']:,}"),
        ("Verified cross-sheet copies removed", f"{dedup['cross_sheet_duplicates_removed']:,}"),
        ("Rows retained", f"{dedup['retained_rows_post_deduplication']:,}"),
        ("Customer-attributed rows", f"{tx['customer_attributed_transactions']:,}"),
        ("Customer commercial-ready rows", f"{tx['customer_commercial_ready_transactions']:,}"),
        ("Unique invoices", f"{inv['total_unique_invoices']:,}"),
        ("Customers with qualifying purchase history", f"{inv['distinct_valid_customers']:,}"),
    ]

    lines = [
        "# Cleaning and Reconciliation Results",
        "",
        "RetenSight checks row counts and financial totals as data moves from the workbook to invoice and customer tables.",
        "",
        "## Data volume",
        "",
        "| Measure | Result |",
        "|---|---:|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    lines.extend([
        "",
        "## Financial reconciliation",
        "",
        "| Measure | Company-wide value |",
        "|---|---:|",
        f"| Gross product sales | {format_gbp(fin['gross_product_sales_gbp'])} |",
        f"| Special commercial charges | {format_gbp(fin['special_commercial_charges_gbp'])} |",
        f"| Gross commercial sales | {format_gbp(fin['gross_sales_gbp'])} |",
        f"| Cancellations and returns | {format_gbp(fin['cancellations_value_gbp'])} |",
        f"| Net commercial value before bad debt | {format_gbp(fin['net_commercial_value_gbp'])} |",
        f"| Bad-debt adjustments | {format_gbp(fin['bad_debt_adjustments_gbp'])} |",
        f"| Net invoice value after bad debt | {format_gbp(fin['all_transactions_net_value_gbp'])} |",
        "",
        "Company-wide totals include unattributed transactions. Customer commercial spend is a separate measure and excludes administrative settlements and bad debt.",
        "",
        "## Integrity checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ])
    for name, passed in invariants.items():
        lines.append(f"| {name} | {'Passed' if passed else '**FAILED**'} |")
    lines.extend([
        "",
        "## Cleaning notes",
        "",
        "- Only confirmed copies duplicated between the two sheets are removed. Repeated rows within a sheet are preserved.",
        "- Transaction lines retain their category and sign so sales, returns and adjustments can be reconciled.",
        "- Free promotional items are kept in the cleaned data but excluded from the customer commercial-ready extract.",
        "- Administrative settlements and bad debt remain in the company accounting audit but are not treated as customer purchases.",
        "",
    ])
    return "\n".join(lines)
