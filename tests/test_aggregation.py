"""Unit tests for invoice-level aggregation and component reconciliation invariants."""

import numpy as np
import pytest

from retensight.aggregation import build_invoice_aggregates
from retensight.cleaning import clean_and_classify_transactions
from retensight.deduplication import resolve_cross_sheet_duplicates


def test_invoice_grain_uniqueness(synthetic_sheets):
    """Verifies that invoice aggregation results in exactly one row per unique invoice."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # Invoices present:
    # 500001, 500002, 500003, 500004, 500005, C500006, C500013, 500007, 500008, A500009, A500014, 500012, 500010, 500011
    # Total unique invoices = 14
    assert len(invoices) == invoices["invoice"].nunique()
    assert len(invoices) == 14


def test_invoice_component_reconciliation_penny_tolerance(synthetic_sheets):
    """Verifies that each category-specific financial component at invoice level

    reconciles to the transaction-level totals within £0.01 tolerance.
    """
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # 1. Product sales component
    tx_prod = cleaned[cleaned["transaction_category"] == "standard_product_sale"]["line_total"].sum()
    assert np.isclose(invoices["product_sales"].sum(), tx_prod, atol=0.01)

    # 2. Special commercial charges component
    tx_spec = cleaned[cleaned["transaction_category"] == "special_commercial_charge"]["line_total"].sum()
    assert np.isclose(invoices["special_charges"].sum(), tx_spec, atol=0.01)

    # 3. Gross sales (product + special charges)
    assert np.isclose(invoices["gross_sales"].sum(), tx_prod + tx_spec, atol=0.01)

    # 4. Cancellation value component
    tx_canc = cleaned[cleaned["transaction_category"] == "cancellation"]["line_total"].sum()
    assert np.isclose(invoices["cancellation_value"].sum(), tx_canc, atol=0.01)

    # 5. Bad debt value component
    tx_debt = cleaned[cleaned["transaction_category"] == "bad_debt_adjustment"]["line_total"].sum()
    assert np.isclose(invoices["bad_debt_value"].sum(), tx_debt, atol=0.01)

    # 6. Overall net value
    assert np.isclose(invoices["net_value"].sum(), cleaned["line_total"].sum(), atol=0.01)

    # 7. Merchandise returns component
    tx_merch_ret = cleaned[
        (~cleaned["is_special_code"])
        & (~cleaned["is_bad_debt"])
        & cleaned["is_cancellation"]
        & (~cleaned["is_zero_price"])
    ]["line_total"].sum()
    assert np.isclose(invoices["merchandise_returns_value"].sum(), tx_merch_ret, atol=0.01)

    # 8. Customer reconciliation residual must be 0.00
    cust_inv = invoices[invoices["has_customer_id"]]
    assert np.allclose(cust_inv["reconciliation_residual"], 0.0, atol=0.01)


def test_positive_cancellation_and_bad_debt_components(synthetic_sheets):
    """Verifies that positive cancellation and bad-debt lines remain in their respective

    category components, not relabeled as ordinary sales.
    """
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # Positive cancellation invoice C500013:
    # line_total is +25.0 -> MUST appear in cancellation_value as +25.0, and gross_sales must be 0.0
    inv_c13 = invoices[invoices["invoice"] == "C500013"].iloc[0]
    assert inv_c13["cancellation_value"] == 25.0
    assert inv_c13["gross_sales"] == 0.0
    assert inv_c13["product_sales"] == 0.0
    assert inv_c13["net_value"] == 25.0
    assert inv_c13["has_positive_cancellation_line"] is True or inv_c13["has_positive_cancellation_line"] == True

    # Positive bad debt invoice A500014:
    # line_total is +50.0 -> MUST appear in bad_debt_value as +50.0, and gross_sales must be 0.0
    inv_a14 = invoices[invoices["invoice"] == "A500014"].iloc[0]
    assert inv_a14["bad_debt_value"] == 50.0
    assert inv_a14["gross_sales"] == 0.0
    assert inv_a14["net_value"] == 50.0

    # Negative bad debt invoice A500009:
    inv_a9 = invoices[invoices["invoice"] == "A500009"].iloc[0]
    assert inv_a9["bad_debt_value"] == -100.0
    assert inv_a9["cancellation_value"] == 0.0
    assert inv_a9["gross_sales"] == 0.0
    assert inv_a9["net_value"] == -100.0

    # Special charge invoice 500012 (POST):
    inv_post = invoices[invoices["invoice"] == "500012"].iloc[0]
    assert inv_post["product_sales"] == 0.0
    assert inv_post["special_charges"] == 15.0
    assert inv_post["gross_sales"] == 15.0
    assert inv_post["net_value"] == 15.0
