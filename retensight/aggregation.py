"""Invoice-level aggregation and reconciliation.

Aggregates transaction line items to the invoice grain, computing product sales,
special commercial charges, gross sales, cancellation values, bad debt values,
and net revenue according to documented transaction classifications.
"""

import logging

import numpy as np
import pandas as pd

from retensight.config import PipelineConfig

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

    # Base grouping by invoice
    grouped = transactions_df.groupby("invoice", sort=False)

    inv_df = grouped.agg(
        invoice_date=("invoice_date", "min"),
        customer_id=("customer_id", "first"),
        country=("country", "first"),
        line_count=("quantity", "count"),
        total_quantity=("quantity", "sum"),
        distinct_items=("stock_code", "nunique"),
        is_cancellation=("is_cancellation", "first"),
        is_bad_debt=("is_bad_debt", "first"),
        source_sheet_nunique=("source_sheet", "nunique"),
        source_sheet_first=("source_sheet", "first"),
    ).reset_index()

    # Aggregate financial components by transaction classification (not simply sign of line_total)
    prod_sales = (
        transactions_df[transactions_df["transaction_category"] == "standard_product_sale"]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("product_sales")
    )
    spec_charges = (
        transactions_df[transactions_df["transaction_category"] == "special_commercial_charge"]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("special_charges")
    )
    canc_val = (
        transactions_df[transactions_df["transaction_category"] == "cancellation"]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("cancellation_value")
    )
    bad_debt_val = (
        transactions_df[transactions_df["transaction_category"] == "bad_debt_adjustment"]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("bad_debt_value")
    )
    pos_canc_flag = (
        transactions_df[transactions_df["is_cancellation"] & (transactions_df["line_total"] > 0)]
        .groupby("invoice", sort=False)["invoice"]
        .count()
        .rename("pos_canc_lines")
    )

    # Sub-component aggregations for explicit traceability
    shipping_val = (
        transactions_df[transactions_df["stock_code"].isin(PipelineConfig.shipping_stock_codes)]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("shipping_value")
    )
    discount_val = (
        transactions_df[transactions_df["stock_code"].isin(PipelineConfig.discount_stock_codes)]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("discount_value")
    )
    manual_val = (
        transactions_df[transactions_df["stock_code"].isin(PipelineConfig.manual_stock_codes)]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("manual_value")
    )
    admin_val = (
        transactions_df[transactions_df["stock_code"].isin(PipelineConfig.administrative_stock_codes)]
        .groupby("invoice", sort=False)["line_total"]
        .sum()
        .rename("admin_settlements_value")
    )

    # Merge financial components onto base invoice DataFrame
    inv_df = inv_df.merge(prod_sales, on="invoice", how="left")
    inv_df = inv_df.merge(spec_charges, on="invoice", how="left")
    inv_df = inv_df.merge(canc_val, on="invoice", how="left")
    inv_df = inv_df.merge(bad_debt_val, on="invoice", how="left")
    inv_df = inv_df.merge(shipping_val, on="invoice", how="left")
    inv_df = inv_df.merge(discount_val, on="invoice", how="left")
    inv_df = inv_df.merge(manual_val, on="invoice", how="left")
    inv_df = inv_df.merge(admin_val, on="invoice", how="left")
    inv_df = inv_df.merge(pos_canc_flag, on="invoice", how="left")

    inv_df["product_sales"] = inv_df["product_sales"].fillna(0.0).round(2)
    inv_df["special_charges"] = inv_df["special_charges"].fillna(0.0).round(2)
    inv_df["gross_sales"] = (inv_df["product_sales"] + inv_df["special_charges"]).round(2)
    inv_df["cancellation_value"] = inv_df["cancellation_value"].fillna(0.0).round(2)
    inv_df["bad_debt_value"] = inv_df["bad_debt_value"].fillna(0.0).round(2)
    inv_df["shipping_value"] = inv_df["shipping_value"].fillna(0.0).round(2)
    inv_df["discount_value"] = inv_df["discount_value"].fillna(0.0).round(2)
    inv_df["manual_value"] = inv_df["manual_value"].fillna(0.0).round(2)
    inv_df["admin_settlements_value"] = inv_df["admin_settlements_value"].fillna(0.0).round(2)

    inv_df["net_value"] = (
        inv_df["gross_sales"] + inv_df["cancellation_value"] + inv_df["bad_debt_value"]
    ).round(2)

    # Primary customer commercial spend measure (excludes bad debt and non-commercial admin settlements)
    inv_df["commercial_net_spend"] = (
        inv_df["net_value"] - inv_df["admin_settlements_value"] - inv_df["bad_debt_value"]
    ).round(2)

    inv_df["has_positive_cancellation_line"] = inv_df["pos_canc_lines"].fillna(0) > 0
    inv_df = inv_df.drop(columns=["pos_canc_lines"])

    # Resolve source sheet label
    inv_df["source_sheet"] = np.where(
        inv_df["source_sheet_nunique"] > 1,
        "mixed",
        inv_df["source_sheet_first"],
    )
    inv_df = inv_df.drop(columns=["source_sheet_nunique", "source_sheet_first"])

    # Customer ID presence flag
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

    # Component-level financial reconciliation against transaction categories (penny tolerance 0.01)
    tx_prod_sales = transactions_df[
        transactions_df["transaction_category"] == "standard_product_sale"
    ]["line_total"].sum()
    tx_spec_charges = transactions_df[
        transactions_df["transaction_category"] == "special_commercial_charge"
    ]["line_total"].sum()
    tx_cancellation = transactions_df[
        transactions_df["transaction_category"] == "cancellation"
    ]["line_total"].sum()
    tx_bad_debt = transactions_df[
        transactions_df["transaction_category"] == "bad_debt_adjustment"
    ]["line_total"].sum()
    tx_net = transactions_df["line_total"].sum()

    assert np.isclose(inv_df["product_sales"].sum(), tx_prod_sales, atol=0.01), (
        f"Product sales component mismatch: {inv_df['product_sales'].sum():.2f} != {tx_prod_sales:.2f}"
    )
    assert np.isclose(inv_df["special_charges"].sum(), tx_spec_charges, atol=0.01), (
        f"Special charges component mismatch: {inv_df['special_charges'].sum():.2f} != {tx_spec_charges:.2f}"
    )
    assert np.isclose(inv_df["cancellation_value"].sum(), tx_cancellation, atol=0.01), (
        f"Cancellation component mismatch: {inv_df['cancellation_value'].sum():.2f} != {tx_cancellation:.2f}"
    )
    assert np.isclose(inv_df["bad_debt_value"].sum(), tx_bad_debt, atol=0.01), (
        f"Bad debt component mismatch: {inv_df['bad_debt_value'].sum():.2f} != {tx_bad_debt:.2f}"
    )
    assert np.isclose(inv_df["net_value"].sum(), tx_net, atol=0.01), (
        f"Net value invariant mismatch: {inv_df['net_value'].sum():.2f} != {tx_net:.2f}"
    )
    assert np.isclose(
        inv_df["commercial_net_spend"] + inv_df["admin_settlements_value"] + inv_df["bad_debt_value"],
        inv_df["net_value"],
        atol=0.01,
    ).all(), "Commercial net spend reconciliation failed at invoice grain."

    logger.info(
        "Built %d invoice aggregate records across %d customers (Customer sales: %d, Cancellations: %d).",
        len(inv_df),
        inv_df["customer_id"].nunique(dropna=True),
        (inv_df["invoice_type"] == "customer_sale").sum(),
        inv_df["is_cancellation"].sum(),
    )

    return inv_df
