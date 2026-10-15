"""Invoice-level aggregation and reconciliation.

Aggregates transaction line items to the invoice grain, computing gross sales,
cancellation values, net revenue, and item quantities without fanouts or
double-counting.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_invoice_aggregates(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates transaction records to the invoice grain.

    Parameters
    ----------
    transactions_df : pd.DataFrame
        Cleaned transaction-level DataFrame.

    Returns
    -------
    pd.DataFrame
        Invoice-level summary table with exactly one row per invoice.
    """
    logger.info("Aggregating %d transactions to invoice grain...", len(transactions_df))

    # Helper aggregations
    # Compute positive (gross) and negative (cancellation) line sums
    pos_mask = transactions_df["line_total"] > 0
    neg_mask = transactions_df["line_total"] < 0

    # Calculate grouped metrics
    grouped = transactions_df.groupby("invoice", sort=False)

    # Base aggregations
    inv_df = grouped.agg(
        invoice_date=("invoice_date", "min"),
        customer_id=("customer_id", "first"),
        country=("country", "first"),
        line_count=("quantity", "count"),
        total_quantity=("quantity", "sum"),
        net_value=("line_total", "sum"),
        distinct_items=("stock_code", "nunique"),
        is_cancellation=("is_cancellation", "first"),
        is_bad_debt=("is_bad_debt", "first"),
        source_sheet_nunique=("source_sheet", "nunique"),
        source_sheet_first=("source_sheet", "first"),
    ).reset_index()

    # Gross sales (positive line totals) per invoice
    gross_sales = (
        transactions_df[pos_mask]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("gross_sales")
    )

    # Cancellation values (negative line totals) per invoice
    cancellation_val = (
        transactions_df[neg_mask]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("cancellation_value")
    )

    # Merge financial components
    inv_df = inv_df.merge(gross_sales, on="invoice", how="left")
    inv_df = inv_df.merge(cancellation_val, on="invoice", how="left")

    inv_df["gross_sales"] = inv_df["gross_sales"].fillna(0.0).round(2)
    inv_df["cancellation_value"] = inv_df["cancellation_value"].fillna(0.0).round(2)
    inv_df["net_value"] = inv_df["net_value"].round(2)

    # Resolve source sheet label
    inv_df["source_sheet"] = np.where(
        inv_df["source_sheet_nunique"] > 1,
        "mixed",
        inv_df["source_sheet_first"],
    )
    inv_df = inv_df.drop(columns=["source_sheet_nunique", "source_sheet_first"])

    # Flags and types
    inv_df["has_customer_id"] = inv_df["customer_id"].notna()

    # Determine invoice_type
    conditions = [
        inv_df["is_bad_debt"],
        inv_df["is_cancellation"] & inv_df["has_customer_id"],
        inv_df["is_cancellation"] & (~inv_df["has_customer_id"]),
        (~inv_df["is_cancellation"]) & (~inv_df["is_bad_debt"]) & (inv_df["total_quantity"] <= 0),
        (~inv_df["is_cancellation"]) & (~inv_df["is_bad_debt"]) & inv_df["has_customer_id"],
    ]
    types = [
        "bad_debt_adjustment",
        "customer_cancellation",
        "unattributed_cancellation",
        "inventory_adjustment",
        "customer_sale",
    ]
    inv_df["invoice_type"] = np.select(conditions, types, default="unattributed_sale")

    # Invariant and fanout checks
    assert len(inv_df) == inv_df["invoice"].nunique(), "Primary key violation: Duplicate invoices found."
    assert inv_df["line_count"].sum() == len(transactions_df), (
        f"Line count invariant failed: {inv_df['line_count'].sum()} != {len(transactions_df)}"
    )
    assert inv_df["total_quantity"].sum() == transactions_df["quantity"].sum(), (
        f"Quantity invariant failed: {inv_df['total_quantity'].sum()} != {transactions_df['quantity'].sum()}"
    )

    # Financial precision reconciliation (allowing for tiny floating point rounding)
    assert np.isclose(inv_df["net_value"].sum(), transactions_df["line_total"].sum(), atol=1.0), (
        f"Revenue invariant failed: {inv_df['net_value'].sum()} != {transactions_df['line_total'].sum()}"
    )

    logger.info(
        "Built %d invoice aggregate records across %d customers (Customer sales: %d, Cancellations: %d).",
        len(inv_df),
        inv_df["customer_id"].nunique(dropna=True),
        (inv_df["invoice_type"] == "customer_sale").sum(),
        inv_df["is_cancellation"].sum(),
    )

    return inv_df
