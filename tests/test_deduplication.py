"""Unit tests for cross-sheet duplicate detection and preservation of same-sheet duplicates."""

from datetime import datetime
import pandas as pd
import pytest

from retensight.deduplication import resolve_cross_sheet_duplicates


def test_cross_sheet_exact_matching(synthetic_sheets):
    """Verifies that exact matching correctly identifies cross-sheet duplicates."""
    df1, df2 = synthetic_sheets
    # In synthetic fixture:
    # df1 has 12 rows, df2 has 5 rows (total 17 raw rows).
    # Expected duplicates to remove from df2:
    # - Row 500002 (1 instance)
    # - Row 500003 (1 instance)
    # - Row 500004 (1 instance out of 2)
    # Total removed = 3 rows. Retained in df2 = 2 rows (1 duplicate of 500004 + 1 new row 500011).
    # Total retained = 12 + 2 = 14 rows.

    combined, audit = resolve_cross_sheet_duplicates(df1, df2)

    assert audit.total_raw_rows == 17
    assert audit.cross_sheet_duplicates_removed == 3
    assert audit.retained_rows == 14
    assert len(combined) == 14


def test_preservation_of_same_sheet_duplicates(synthetic_sheets):
    """Verifies that legitimate repeated rows within Sheet 1 and Sheet 2 are preserved."""
    df1, df2 = synthetic_sheets
    combined, audit = resolve_cross_sheet_duplicates(df1, df2)

    # In df1, invoice 500005 has 2 identical rows. Both must remain!
    inv_500005 = combined[combined["Invoice"] == "500005"]
    assert len(inv_500005) == 2, "Same-sheet duplicates in Sheet 1 were erroneously removed!"

    # In df2, invoice 500004 had 2 identical rows, while df1 had 1.
    # 1 matched df1 and was dropped, but the 2nd instance in df2 must be retained!
    inv_500004 = combined[combined["Invoice"] == "500004"]
    # 1 from df1 + 1 retained from df2 = 2
    assert len(inv_500004) == 2, "Surplus duplicate in Sheet 2 was erroneously removed!"


def test_multiplicity_handling():
    """Explicit test for multiplicity:

    If S1 has 3 identical copies and S2 has 2 -> remove 2 from S2.
    If S1 has 2 identical copies and S2 has 3 -> remove 2 from S2, retain 1 in S2.
    """
    cols = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    row_a = ("INV_A", "101", "Item A", 1, datetime(2010, 1, 1), 10.0, 9999, "UK")
    row_b = ("INV_B", "102", "Item B", 2, datetime(2010, 1, 2), 20.0, 8888, "UK")

    # S1: 3 copies of A, 2 copies of B
    df1 = pd.DataFrame([row_a] * 3 + [row_b] * 2, columns=cols)
    # S2: 2 copies of A, 3 copies of B
    df2 = pd.DataFrame([row_a] * 2 + [row_b] * 3, columns=cols)

    combined, audit = resolve_cross_sheet_duplicates(df1, df2)

    # For A: min(3, 2) = 2 removed from S2 -> 0 remain from S2. S1 has 3. Total A = 3.
    # For B: min(2, 3) = 2 removed from S2 -> 1 remains from S2. S1 has 2. Total B = 3.
    # Total removed = 2 + 2 = 4.
    # Total retained = 5 (from df1) + 1 (from df2) = 6.
    assert audit.cross_sheet_duplicates_removed == 4
    assert audit.retained_rows == 6
    assert len(combined[combined["Invoice"] == "INV_A"]) == 3
    assert len(combined[combined["Invoice"] == "INV_B"]) == 3


def test_nan_customer_id_cross_sheet_equality():
    """Verifies that rows with NaN Customer ID match as identical cross-sheet duplicates."""
    cols = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    row_nan = ("INV_NAN", "103", "Item Null", 1, datetime(2010, 1, 1), 5.0, None, "UK")

    df1 = pd.DataFrame([row_nan], columns=cols)
    df2 = pd.DataFrame([row_nan], columns=cols)

    combined, audit = resolve_cross_sheet_duplicates(df1, df2)
    assert audit.cross_sheet_duplicates_removed == 1
    assert len(combined) == 1
