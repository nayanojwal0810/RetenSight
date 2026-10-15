"""Unit tests for transaction cleaning, type normalization, and categorization."""

import pandas as pd
import pytest

from retensight.cleaning import clean_and_classify_transactions
from retensight.deduplication import resolve_cross_sheet_duplicates


def test_column_normalization_and_types(synthetic_sheets):
    """Verifies that columns are normalized and typed properly."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    expected_cols = [
        "invoice",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "price",
        "customer_id",
        "country",
        "source_sheet",
        "source_row_num",
        "line_total",
        "is_cancellation",
        "is_bad_debt",
        "is_zero_price",
        "is_negative_price",
        "has_customer_id",
        "is_special_code",
        "transaction_category",
        "is_customer_analysis_ready",
    ]
    for col in expected_cols:
        assert col in cleaned.columns, f"Missing expected column: {col}"

    assert cleaned["quantity"].dtype == "int64"
    assert cleaned["price"].dtype == "float64"
    assert str(cleaned["customer_id"].dtype) == "Int64"


def test_line_total_calculation(synthetic_sheets):
    """Verifies that line_total equals quantity * price."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    expected_totals = (cleaned["quantity"] * cleaned["price"]).round(2)
    assert (cleaned["line_total"] == expected_totals).all()


def test_cancellation_classification(synthetic_sheets):
    """Verifies that cancellation invoices starting with 'C' are classified correctly."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    cancellation_rows = cleaned[cleaned["invoice"] == "C500006"]
    assert len(cancellation_rows) == 1
    assert cancellation_rows["is_cancellation"].iloc[0] is True or cancellation_rows["is_cancellation"].iloc[0] == True
    assert cancellation_rows["transaction_category"].iloc[0] == "cancellation"
    assert cancellation_rows["line_total"].iloc[0] < 0


def test_bad_debt_adjustment_classification(synthetic_sheets):
    """Verifies bad debt adjustment invoices starting with 'A'."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    bad_debt = cleaned[cleaned["invoice"] == "A500009"]
    assert len(bad_debt) == 1
    assert bad_debt["is_bad_debt"].iloc[0] is True or bad_debt["is_bad_debt"].iloc[0] == True
    assert bad_debt["transaction_category"].iloc[0] == "bad_debt_adjustment"
    assert bad_debt["is_customer_analysis_ready"].iloc[0] is False or bad_debt["is_customer_analysis_ready"].iloc[0] == False


def test_zero_price_differentiation(synthetic_sheets):
    """Verifies inventory write-offs vs promotional freebies."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    # 500007: damage write-off (no customer)
    damages = cleaned[cleaned["invoice"] == "500007"]
    assert damages["transaction_category"].iloc[0] == "inventory_adjustment"
    assert bool(damages["is_customer_analysis_ready"].iloc[0]) is False

    # 500008: free gift (customer 12349)
    freebie = cleaned[cleaned["invoice"] == "500008"]
    assert freebie["transaction_category"].iloc[0] == "promotional_freebie"
    assert bool(freebie["is_customer_analysis_ready"].iloc[0]) is True
