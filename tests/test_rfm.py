"""Unit and edge-case tests for customer RFM feature computation and segmentation."""

from datetime import timedelta
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pytest

from retensight.rfm import (
    CRM_SEGMENT_RULES,
    assign_crm_segment,
    build_all_rfm_snapshots,
    compute_customer_rfm_snapshot,
    evaluate_admin_settlements_sensitivity,
    extract_qualifying_purchases,
    generate_crm_segment_decision_table,
    get_frequency_score,
    save_rfm_summary_reports,
    summarize_rfm_snapshots,
)


@pytest.fixture
def synthetic_invoices_for_rfm() -> pd.DataFrame:
    """Creates a controlled synthetic invoice aggregates dataset to test RFM edge cases.

    Scenarios covered:
    - Customer 1001: Repeat buyer with 3 standard purchase orders over 60 days.
    - Customer 1002: One-time buyer with 1 order (tested for F=1 scoring).
    - Customer 1003: Charge-only customer (postage fee only; product_sales=0) -> excluded from qualifying purchases.
    - Customer 1004: Cancellation only -> excluded from qualifying purchases.
    - Customer 1005: Returned more than purchased -> net_spend <= 0 -> Negative or Zero Spend segment.
    - Customer 1007: Placed 2 separate orders on the exact same date (same-day orders test).
    - Customer 1008: Has an administrative settlement (CRUK / ADJUST) -> isolated from commercial spend.
    - Unattributed invoices (missing customer_id).
    """
    records = [
        # Customer 1001: 3 purchases (Order 1: 100 gross, Order 2: 55 gross, Order 3: 200 gross) -> AOV = 355 / 3 = 118.33
        {
            "invoice": "INV001",
            "invoice_date": pd.Timestamp("2010-01-01 10:00:00"),
            "customer_id": 1001,
            "country": "United Kingdom",
            "line_count": 2,
            "total_quantity": 5,
            "distinct_items": 2,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 100.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 100.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 100.0,
            "commercial_net_spend": 100.0,
            "invoice_type": "customer_sale",
        },
        {
            "invoice": "INV002",
            "invoice_date": pd.Timestamp("2010-02-01 10:00:00"),
            "customer_id": 1001,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 2,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 50.0,
            "special_charges": 5.0,
            "shipping_value": 5.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 55.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 55.0,
            "commercial_net_spend": 55.0,
            "invoice_type": "customer_sale",
        },
        {
            "invoice": "INV003",
            "invoice_date": pd.Timestamp("2010-03-01 10:00:00"),
            "customer_id": 1001,
            "country": "United Kingdom",
            "line_count": 3,
            "total_quantity": 10,
            "distinct_items": 3,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 200.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 200.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 200.0,
            "commercial_net_spend": 200.0,
            "invoice_type": "customer_sale",
        },
        # Customer 1002: One-time buyer (F=1)
        {
            "invoice": "INV004",
            "invoice_date": pd.Timestamp("2010-02-15 11:00:00"),
            "customer_id": 1002,
            "country": "Germany",
            "line_count": 1,
            "total_quantity": 1,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 30.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 30.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 30.0,
            "commercial_net_spend": 30.0,
            "invoice_type": "customer_sale",
        },
        # Customer 1003: Charge-only invoice (postage fee only, product_sales == 0)
        {
            "invoice": "INV005",
            "invoice_date": pd.Timestamp("2010-02-20 12:00:00"),
            "customer_id": 1003,
            "country": "France",
            "line_count": 1,
            "total_quantity": 1,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 0.0,
            "special_charges": 25.0,
            "shipping_value": 25.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 25.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 25.0,
            "commercial_net_spend": 25.0,
            "invoice_type": "customer_sale",
        },
        # Customer 1004: Cancellation only
        {
            "invoice": "CINV006",
            "invoice_date": pd.Timestamp("2010-02-25 14:00:00"),
            "customer_id": 1004,
            "country": "Spain",
            "line_count": 1,
            "total_quantity": -5,
            "distinct_items": 1,
            "is_cancellation": True,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 0.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 0.0,
            "cancellation_value": -100.0,
            "bad_debt_value": 0.0,
            "net_value": -100.0,
            "commercial_net_spend": -100.0,
            "invoice_type": "customer_cancellation",
        },
        # Customer 1005: 1 small purchase + 1 huge cancellation -> net spend < 0
        {
            "invoice": "INV007",
            "invoice_date": pd.Timestamp("2010-01-10 09:00:00"),
            "customer_id": 1005,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 1,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 20.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 20.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 20.0,
            "commercial_net_spend": 20.0,
            "invoice_type": "customer_sale",
        },
        {
            "invoice": "CINV008",
            "invoice_date": pd.Timestamp("2010-02-10 09:00:00"),
            "customer_id": 1005,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": -10,
            "distinct_items": 1,
            "is_cancellation": True,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 0.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 0.0,
            "cancellation_value": -150.0,
            "bad_debt_value": 0.0,
            "net_value": -150.0,
            "commercial_net_spend": -150.0,
            "invoice_type": "customer_cancellation",
        },
        # Customer 1007: Same-day separate orders (2 distinct invoices on 2010-03-05)
        {
            "invoice": "INV009",
            "invoice_date": pd.Timestamp("2010-03-05 10:15:00"),
            "customer_id": 1007,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 4,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 40.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 40.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 40.0,
            "commercial_net_spend": 40.0,
            "invoice_type": "customer_sale",
        },
        {
            "invoice": "INV010",
            "invoice_date": pd.Timestamp("2010-03-05 16:30:00"),
            "customer_id": 1007,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 6,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 60.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 60.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 60.0,
            "commercial_net_spend": 60.0,
            "invoice_type": "customer_sale",
        },
        # Customer 1008: Purchase + Administrative settlement
        {
            "invoice": "INV011",
            "invoice_date": pd.Timestamp("2010-01-20 11:00:00"),
            "customer_id": 1008,
            "country": "United Kingdom",
            "line_count": 2,
            "total_quantity": 10,
            "distinct_items": 2,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 500.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 500.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 500.0,
            "commercial_net_spend": 500.0,
            "invoice_type": "customer_sale",
        },
        {
            "invoice": "CINV012",
            "invoice_date": pd.Timestamp("2010-02-20 11:00:00"),
            "customer_id": 1008,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": -1,
            "distinct_items": 1,
            "is_cancellation": True,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 0.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": -100.0,  # e.g. CRUK commission or adjustment
            "gross_sales": 0.0,
            "cancellation_value": -100.0,
            "bad_debt_value": 0.0,
            "net_value": -100.0,
            "commercial_net_spend": 0.0,  # Excluded from commercial net spend!
            "invoice_type": "customer_cancellation",
        },
        # Future invoice after cutoff (2010-04-15) for testing leakage and target labeling
        {
            "invoice": "INV013",
            "invoice_date": pd.Timestamp("2010-04-15 10:00:00"),
            "customer_id": 1001,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 5,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 75.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 75.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 75.0,
            "commercial_net_spend": 75.0,
            "invoice_type": "customer_sale",
        },
        # Dataset end anchor invoice (ensures full 90d forward window observation from 2010-03-31)
        {
            "invoice": "INV014",
            "invoice_date": pd.Timestamp("2010-07-01 10:00:00"),
            "customer_id": 1002,
            "country": "Germany",
            "line_count": 1,
            "total_quantity": 2,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 20.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "gross_sales": 20.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 20.0,
            "commercial_net_spend": 20.0,
            "invoice_type": "customer_sale",
        },
    ]
    df = pd.DataFrame(records)
    if "merchandise_returns_value" not in df.columns:
        df["merchandise_returns_value"] = np.where(
            df["is_cancellation"] & (df["admin_settlements_value"] == 0.0),
            df["cancellation_value"],
            0.0,
        )
    return df


def test_qualifying_purchases_filtering(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Verifies that charge-only invoices, cancellations, and unattributed rows do not qualify as purchase events."""
    cutoff = pd.Timestamp("2010-03-31 23:59:59")
    qualifying = extract_qualifying_purchases(synthetic_invoices_for_rfm, as_of_date=cutoff)

    qualifying_cust_ids = set(qualifying["customer_id"].unique())

    # Customers 1001, 1002, 1005, 1007, 1008 have valid product purchases
    assert 1001 in qualifying_cust_ids
    assert 1002 in qualifying_cust_ids
    assert 1005 in qualifying_cust_ids
    assert 1007 in qualifying_cust_ids
    assert 1008 in qualifying_cust_ids

    # Customer 1003 had only postage charges (product_sales == 0) -> must NOT qualify
    assert 1003 not in qualifying_cust_ids

    # Customer 1004 had only cancellations -> must NOT qualify
    assert 1004 not in qualifying_cust_ids

    # Unattributed rows must NOT qualify
    assert qualifying["customer_id"].isna().sum() == 0

    # Cancellations must NOT qualify
    assert qualifying["is_cancellation"].any() is np.False_


def test_multi_line_and_same_day_invoice_handling(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Verifies that multi-line invoices aggregate to 1 event and same-day distinct invoices

    increment invoice frequency while keeping distinct_purchase_days at 1.
    """
    cutoff = pd.Timestamp("2010-03-31 23:59:59")
    rfm_df = compute_customer_rfm_snapshot(
        synthetic_invoices_for_rfm,
        snapshot_date=cutoff,
        forward_target_days=90,
    )

    # Customer 1007 placed 2 invoices on 2010-03-05
    c1007 = rfm_df[rfm_df["customer_id"] == 1007].iloc[0]
    assert c1007["frequency"] == 2
    assert c1007["distinct_purchase_days"] == 1


def test_conventional_aov_and_spend_components(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Verifies that merchandise AOV and commercial order value are calculated strictly across qualifying purchase orders

    and customer commercial spend reconciles with admin settlements.
    """
    cutoff = pd.Timestamp("2010-03-31 23:59:59")
    rfm_df = compute_customer_rfm_snapshot(
        synthetic_invoices_for_rfm,
        snapshot_date=cutoff,
        forward_target_days=90,
    )

    # Customer 1001: 3 orders (merchandise: £100, £50, £200 -> total = £350; shipping: £5 -> total = £355)
    c1001 = rfm_df[rfm_df["customer_id"] == 1001].iloc[0]
    assert c1001["frequency"] == 3
    assert c1001["qualifying_merchandise_sales"] == 350.0
    assert c1001["qualifying_commercial_sales"] == 355.0
    assert np.isclose(c1001["merchandise_aov"], 116.67, atol=0.01)
    assert np.isclose(c1001["commercial_order_value"], 118.33, atol=0.01)
    assert np.isclose(c1001["avg_order_value"], 116.67, atol=0.01)
    assert c1001["net_commercial_spend"] == 355.0
    assert c1001["monetary_shipping"] == 5.0
    assert np.isclose(c1001["reconciliation_residual"], 0.0, atol=0.01)

    # Customer 1008: Purchase £500, Admin settlement -£100
    c1008 = rfm_df[rfm_df["customer_id"] == 1008].iloc[0]
    assert c1008["net_commercial_spend"] == 500.0  # Admin settlement excluded from commercial spend!
    assert c1008["monetary_admin_settlements"] == -100.0
    assert c1008["total_account_balance"] == 400.0  # Reconciles to account balance
    assert np.isclose(c1008["reconciliation_residual"], 0.0, atol=0.01)


def test_merchandise_aov_independent_of_admin_settlements() -> None:
    """Verifies that administrative settlements (CRUK, BANK CHARGES, ADJUST)

    do not alter merchandise AOV or commercial order value.
    """
    base_inv = [
        {
            "invoice": "INV_AOV_1",
            "invoice_date": pd.Timestamp("2010-01-15 10:00:00"),
            "customer_id": 9999,
            "country": "United Kingdom",
            "line_count": 3,
            "total_quantity": 5,
            "distinct_items": 3,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 150.0,
            "special_charges": 65.0,  # 15.0 shipping + 50.0 bank charges
            "shipping_value": 15.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 50.0,  # Administrative fee on invoice
            "merchandise_returns_value": 0.0,
            "gross_sales": 215.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 215.0,
            "commercial_net_spend": 165.0,  # 150.0 merch + 15.0 shipping
            "invoice_type": "customer_sale",
        },
        # Anchor invoice
        {
            "invoice": "INV_AOV_ANCHOR",
            "invoice_date": pd.Timestamp("2010-06-01 10:00:00"),
            "customer_id": 9999,
            "country": "United Kingdom",
            "line_count": 1,
            "total_quantity": 1,
            "distinct_items": 1,
            "is_cancellation": False,
            "is_bad_debt": False,
            "has_customer_id": True,
            "product_sales": 50.0,
            "special_charges": 0.0,
            "shipping_value": 0.0,
            "discount_value": 0.0,
            "manual_value": 0.0,
            "admin_settlements_value": 0.0,
            "merchandise_returns_value": 0.0,
            "gross_sales": 50.0,
            "cancellation_value": 0.0,
            "bad_debt_value": 0.0,
            "net_value": 50.0,
            "commercial_net_spend": 50.0,
            "invoice_type": "customer_sale",
        },
    ]

    df_base = pd.DataFrame(base_inv)
    cutoff = pd.Timestamp("2010-02-01 23:59:59")
    rfm_base = compute_customer_rfm_snapshot(df_base, snapshot_date=cutoff, forward_target_days=90)
    row_base = rfm_base[rfm_base["customer_id"] == 9999].iloc[0]

    assert row_base["merchandise_aov"] == 150.0
    assert row_base["commercial_order_value"] == 165.0
    assert row_base["avg_order_value"] == 150.0

    # Modify the administrative settlement to £500.0 (e.g. large clerical adjustment)
    df_altered = df_base.copy()
    df_altered.loc[0, "admin_settlements_value"] = 500.0
    df_altered.loc[0, "net_value"] = 665.0
    # Commercial net spend remains £165.0 (£665.0 - £500.0)

    rfm_altered = compute_customer_rfm_snapshot(df_altered, snapshot_date=cutoff, forward_target_days=90)
    row_altered = rfm_altered[rfm_altered["customer_id"] == 9999].iloc[0]

    # Altering the administrative settlement has ZERO effect on merchandise AOV or commercial order value
    assert row_altered["merchandise_aov"] == 150.0
    assert row_altered["commercial_order_value"] == 165.0
    assert row_altered["avg_order_value"] == 150.0
    assert row_altered["merchandise_aov"] == row_base["merchandise_aov"]
    assert row_altered["commercial_order_value"] == row_base["commercial_order_value"]


def test_feature_leakage_prevention_and_unobserved_targets(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Verifies that transactions occurring strictly after snapshot cutoff do not leak

    into historical RFM features, and unobserved future windows are marked <NA>.
    """
    cutoff = pd.Timestamp("2010-03-31 23:59:59")
    rfm_df = compute_customer_rfm_snapshot(
        synthetic_invoices_for_rfm,
        snapshot_date=cutoff,
        forward_target_days=90,
    )

    c1001 = rfm_df[rfm_df["customer_id"] == 1001].iloc[0]
    # As of 2010-03-31, Customer 1001 made 3 purchases (£355 net commercial spend)
    # The 4th purchase occurred on 2010-04-15 (£75.0) and must NOT be in historical features
    assert c1001["frequency"] == 3
    assert c1001["net_commercial_spend"] == 355.0
    assert c1001["last_purchase_date"] == pd.Timestamp("2010-03-01 10:00:00")

    # The 2010-04-15 purchase falls within the 90-day forward window (2010-03-31 to 2010-06-29)
    assert c1001["target_repeat_purchase_90d"] == 1
    assert c1001["target_spend_90d"] == 75.0

    # Unobserved horizon test: if horizon exceeds dataset max date (2010-07-01), target is marked <NA>
    unobserved_rfm = compute_customer_rfm_snapshot(
        synthetic_invoices_for_rfm,
        snapshot_date=pd.Timestamp("2010-06-01 23:59:59"),
        forward_target_days=90,  # 90d reaches 2010-08-30 > 2010-07-01
    )
    assert not bool(unobserved_rfm["is_target_window_observed"].iloc[0])
    assert unobserved_rfm["target_repeat_purchase_90d"].isna().all()


def test_monetary_aware_segmentation_distinctions() -> None:
    """Verifies that monetary value materially governs segment assignment:

    - Low-value high-cadence shoppers are NOT Champions.
    - High-value inactive shoppers are prioritized over low-value inactive shoppers.
    - Recent one-time low spenders are New Customers; high spenders are Promising.
    """
    # 1. High Recency, High Frequency, but LOW monetary value (M=1) -> Promising (NOT Champion!)
    seg_low_m = assign_crm_segment(r=5, f=5, m=1, net_commercial_spend=10.0)
    assert seg_low_m != "Champions"
    assert seg_low_m == "Promising"

    # Moderate monetary value (M=2) -> Loyal Customer (NOT Champion!)
    seg_mid_m = assign_crm_segment(r=5, f=5, m=2, net_commercial_spend=250.0)
    assert seg_mid_m != "Champions"
    assert seg_mid_m == "Loyal Customers"

    # High monetary value (M=5) -> Champion!
    seg_champ = assign_crm_segment(r=5, f=5, m=5, net_commercial_spend=5000.0)
    assert seg_champ == "Champions"

    # 2. Inactive customers (R=1, F=3):
    # High monetary value (M=5) -> Can't Lose Them!
    seg_vip_dormant = assign_crm_segment(r=1, f=3, m=5, net_commercial_spend=8000.0)
    assert seg_vip_dormant == "Can't Lose Them"

    # Moderate monetary value (M=3) -> At Risk
    seg_mid_dormant = assign_crm_segment(r=1, f=3, m=3, net_commercial_spend=400.0)
    assert seg_mid_dormant == "At Risk"

    # Low monetary value (M=1) -> Hibernating
    seg_low_dormant = assign_crm_segment(r=1, f=3, m=1, net_commercial_spend=50.0)
    assert seg_low_dormant == "Hibernating"

    # 3. Recent One-time buyers (R in [4, 5], F=1):
    # Low spend (M in [1, 2]) -> New Customers (entry-level first-time buyers)
    assert assign_crm_segment(r=5, f=1, m=1, net_commercial_spend=15.0) == "New Customers"
    assert assign_crm_segment(r=4, f=1, m=2, net_commercial_spend=40.0) == "New Customers"

    # High spend (M in [3, 4, 5]) -> Promising (high-ticket first-time buyers)
    assert assign_crm_segment(r=5, f=1, m=3, net_commercial_spend=150.0) == "Promising"
    assert assign_crm_segment(r=4, f=1, m=5, net_commercial_spend=2000.0) == "Promising"

    # 4. Lapsed one-time buyers (R=1, F=1):
    # High spend -> At Risk
    seg_onetime_whale = assign_crm_segment(r=1, f=1, m=5, net_commercial_spend=10000.0)
    assert seg_onetime_whale == "At Risk"

    # Low spend -> Lost
    seg_lost = assign_crm_segment(r=1, f=1, m=1, net_commercial_spend=20.0)
    assert seg_lost == "Lost"


def test_all_125_rfm_cells_exhaustively_covered() -> None:
    """Verifies that all 125 possible score combinations (R in 1..5, F in 1..5, M in 1..5)

    assert the exact expected segment defined in CRM_SEGMENT_RULES, and non-positive spend maps to its dedicated segment.
    """
    decision_table = generate_crm_segment_decision_table()
    assert len(decision_table) == 126, f"Expected 126 decision table rows, got {len(decision_table)}"

    # Assert EVERY combination matches the single source of truth lookup
    for r in range(1, 6):
        for f in range(1, 6):
            for m in range(1, 6):
                expected = CRM_SEGMENT_RULES[(r, f, m)]
                actual = assign_crm_segment(r, f, m, net_commercial_spend=100.0)
                assert actual == expected, f"Mismatch at ({r}, {f}, {m}): expected '{expected}', got '{actual}'"

    # Non-positive net spend checks
    assert assign_crm_segment(5, 5, 5, net_commercial_spend=-10.0) == "Negative or Zero Spend"
    assert assign_crm_segment(1, 1, 1, net_commercial_spend=0.0) == "Negative or Zero Spend"
    assert assign_crm_segment(3, 3, 0, net_commercial_spend=100.0) == "Negative or Zero Spend"


def test_independent_component_reconciliation_zero_residual(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Demonstrates that reconciliation is correct for real component definitions,

    with zero residual rather than forced balancing.
    """
    cutoff = pd.Timestamp("2010-03-31 23:59:59")
    rfm_df = compute_customer_rfm_snapshot(synthetic_invoices_for_rfm, snapshot_date=cutoff)

    # Every customer must have reconciliation_residual == 0.00
    assert np.allclose(rfm_df["reconciliation_residual"], 0.0, atol=0.01)

    # Net commercial spend must equal the sum of its independent components
    reconciled_sum = (
        rfm_df["monetary_merchandise_sales"]
        + rfm_df["monetary_merchandise_returns"]
        + rfm_df["monetary_shipping"]
        + rfm_df["monetary_discounts"]
        + rfm_df["monetary_manual_charges"]
    )
    assert np.allclose(rfm_df["net_commercial_spend"], reconciled_sum, atol=0.01)

    # Account balance must equal net commercial spend plus administrative settlements
    account_balance_sum = rfm_df["net_commercial_spend"] + rfm_df["monetary_admin_settlements"]
    assert np.allclose(rfm_df["total_account_balance"], account_balance_sum, atol=0.01)


def test_rfm_summary_reports_export(synthetic_invoices_for_rfm: pd.DataFrame) -> None:
    """Verifies multi-cutoff summary generation, decision table export, and report saving."""
    cutoff = "2010-03-31 23:59:59"
    snapshot = compute_customer_rfm_snapshot(synthetic_invoices_for_rfm, snapshot_date=cutoff)
    snapshots = {"2010-03-31": snapshot}

    summary = summarize_rfm_snapshots(snapshots, invoices_df=synthetic_invoices_for_rfm)
    assert "cutoffs" in summary
    assert "2010-03-31" in summary["cutoffs"]
    assert "admin_settlements_sensitivity" in summary
    assert "crm_segment_decision_table" in summary
    assert len(summary["crm_segment_decision_table"]) == 126

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        json_file = tmp_path / "rfm_summary.json"
        md_file = tmp_path / "rfm_summary.md"
        dec_json = tmp_path / "crm_segment_decision_table.json"
        dec_csv = tmp_path / "crm_segment_decision_table.csv"

        save_rfm_summary_reports(summary, json_path=json_file, md_path=md_file)
        assert json_file.exists()
        assert md_file.exists()
        assert dec_json.exists()
        assert dec_csv.exists()
        assert json_file.stat().st_size > 0
        assert md_file.stat().st_size > 0
        assert dec_json.stat().st_size > 0
        assert dec_csv.stat().st_size > 0
