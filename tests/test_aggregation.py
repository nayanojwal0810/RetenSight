"""Unit tests for invoice-level aggregation and reconciliation invariants."""

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

    # In synthetic data, invoices are:
    # 500001, 500002, 500003, 500004, 500005, C500006, 500007, 500008, A500009, 500010, 500011
    # Total unique invoices = 11
    assert len(invoices) == 11
    assert invoices["invoice"].nunique() == 11


def test_invoice_reconciliation_invariants(synthetic_sheets):
    """Verifies line count, total quantity, and revenue reconciliation between transactions and invoices."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # 1. Line count invariant
    assert invoices["line_count"].sum() == len(cleaned)

    # 2. Total quantity invariant
    assert invoices["total_quantity"].sum() == cleaned["quantity"].sum()

    # 3. Net value invariant
    assert np.isclose(invoices["net_value"].sum(), cleaned["line_total"].sum(), atol=0.01)


def test_gross_sales_and_cancellation_separation(synthetic_sheets):
    """Verifies gross sales and cancellation values are correctly separated."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # Standard sale invoice 500001: 2 * 5.0 = 10.0 gross, 0 cancellation
    inv_1 = invoices[invoices["invoice"] == "500001"].iloc[0]
    assert inv_1["gross_sales"] == 10.0
    assert inv_1["cancellation_value"] == 0.0
    assert inv_1["net_value"] == 10.0
    assert inv_1["invoice_type"] == "customer_sale"

    # Cancellation invoice C500006: 0 gross, -5.0 cancellation
    inv_c = invoices[invoices["invoice"] == "C500006"].iloc[0]
    assert inv_c["gross_sales"] == 0.0
    assert inv_c["cancellation_value"] == -5.0
    assert inv_c["net_value"] == -5.0
    assert inv_c["invoice_type"] == "customer_cancellation"
