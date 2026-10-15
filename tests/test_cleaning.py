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
        "is_customer_attributed",
        "is_commercial_customer_ready",
        "is_customer_analysis_ready",
    ]
    for col in expected_cols:
        assert col in cleaned.columns, f"Missing expected column: {col}"

    assert cleaned["quantity"].dtype == "int64"
    assert cleaned["price"].dtype == "float64"
    assert str(cleaned["customer_id"].dtype) == "Int64"


def test_special_commercial_charge_distinction(synthetic_sheets):
    """Verifies that special stock codes with positive prices are classified as special_commercial_charge,

    distinguishable from standard_product_sale.
    """
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    # 500012: POSTAGE (code POST, price 15.0)
    postage = cleaned[cleaned["invoice"] == "500012"]
    assert len(postage) == 1
    assert postage["transaction_category"].iloc[0] == "special_commercial_charge"
    assert postage["is_special_code"].iloc[0] is True or postage["is_special_code"].iloc[0] == True
    assert postage["line_total"].iloc[0] == 15.0

    # 500001: standard product sale (code 85048)
    product = cleaned[cleaned["invoice"] == "500001"]
    assert len(product) == 1
    assert product["transaction_category"].iloc[0] == "standard_product_sale"
    assert product["is_special_code"].iloc[0] is False or product["is_special_code"].iloc[0] == False


def test_positive_and_negative_cancellations(synthetic_sheets):
    """Verifies that all cancellation invoices (including positive lines) remain in cancellation category."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    # C500006: standard return (qty < 0, line_total < 0)
    neg_canc = cleaned[cleaned["invoice"] == "C500006"]
    assert len(neg_canc) == 1
    assert neg_canc["transaction_category"].iloc[0] == "cancellation"
    assert neg_canc["line_total"].iloc[0] < 0

    # C500013: positive cancellation line (qty > 0, price > 0, line_total > 0)
    pos_canc = cleaned[cleaned["invoice"] == "C500013"]
    assert len(pos_canc) == 1
    assert pos_canc["transaction_category"].iloc[0] == "cancellation"
    assert pos_canc["line_total"].iloc[0] > 0
    assert pos_canc["is_cancellation"].iloc[0] is True or pos_canc["is_cancellation"].iloc[0] == True


def test_positive_and_negative_bad_debt(synthetic_sheets):
    """Verifies that both positive and negative bad-debt lines remain in bad_debt_adjustment category."""
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    # A500009: negative price
    neg_debt = cleaned[cleaned["invoice"] == "A500009"]
    assert len(neg_debt) == 1
    assert neg_debt["transaction_category"].iloc[0] == "bad_debt_adjustment"
    assert neg_debt["line_total"].iloc[0] == -100.0

    # A500014: positive price
    pos_debt = cleaned[cleaned["invoice"] == "A500014"]
    assert len(pos_debt) == 1
    assert pos_debt["transaction_category"].iloc[0] == "bad_debt_adjustment"
    assert pos_debt["line_total"].iloc[0] == 50.0


def test_promotional_freebie_and_commercial_readiness(synthetic_sheets):
    """Verifies that promotional freebies are retained in cleaned data with customer ID,

    but strictly excluded from commercial/model-ready customer extract.
    """
    df1, df2 = synthetic_sheets
    combined, _ = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)

    # 500008: promotional freebie (Price == 0, Customer ID populated)
    freebie = cleaned[cleaned["invoice"] == "500008"]
    assert len(freebie) == 1
    assert freebie["transaction_category"].iloc[0] == "promotional_freebie"
    assert bool(freebie["has_customer_id"].iloc[0]) is True
    assert bool(freebie["is_customer_attributed"].iloc[0]) is True
    assert bool(freebie["is_commercial_customer_ready"].iloc[0]) is False

    # Check total commercial customer-ready count vs attributed count
    total_attributed = cleaned["has_customer_id"].sum()
    commercial_ready = cleaned["is_commercial_customer_ready"].sum()
    freebies = (cleaned["transaction_category"] == "promotional_freebie").sum()
    assert commercial_ready == total_attributed - freebies
