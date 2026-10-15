"""Integration and end-to-end pipeline execution tests."""

import numpy as np
from pathlib import Path
import pandas as pd
import pytest

from retensight.pipeline import run_pipeline


def test_pipeline_on_synthetic_workbook(tmp_path):
    """Executes the full pipeline end-to-end on a generated multi-sheet workbook."""
    input_file = tmp_path / "synthetic_retail.xlsx"
    out_dir = tmp_path / "processed"
    rep_dir = tmp_path / "reports"

    cols = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    s1_rows = [
        (5001, "A1", "Item 1", 2, "2010-01-01 10:00:00", 10.0, 11111, "UK"),
        (5002, "A2", "Item 2", 1, "2010-12-05 12:00:00", 20.0, 22222, "UK"),  # cross-sheet dup
        ("C5003", "A1", "Item 1", -1, "2010-01-02 10:00:00", 10.0, 11111, "UK"),
        (5005, "FREE1", "Free gift", 1, "2010-01-03 10:00:00", 0.0, 11111, "UK"),  # freebie
    ]
    s2_rows = [
        (5002, "A2", "Item 2", 1, "2010-12-05 12:00:00", 20.0, 22222, "UK"),  # duplicate copy
        (5004, "A3", "Item 3", 5, "2011-01-01 11:00:00", 5.0, 33333, "UK"),
    ]

    with pd.ExcelWriter(input_file, engine="openpyxl") as writer:
        pd.DataFrame(s1_rows, columns=cols).to_excel(writer, sheet_name="Year 2009-2010", index=False)
        pd.DataFrame(s2_rows, columns=cols).to_excel(writer, sheet_name="Year 2010-2011", index=False)

    exit_code = run_pipeline(
        input_path=input_file,
        output_dir=out_dir,
        reports_dir=rep_dir,
        export_csv=True,
        engine="openpyxl",
    )

    assert exit_code == 0
    assert (out_dir / "cleaned_transactions.parquet").exists()
    assert (out_dir / "customer_transactions.parquet").exists()
    assert (out_dir / "invoice_aggregates.parquet").exists()
    assert (out_dir / "invoice_aggregates.csv").exists()
    assert (rep_dir / "data_quality_audit.json").exists()
    assert (rep_dir / "cleaning_and_reconciliation_summary.md").exists()

    # Reopen outputs and verify schemas and values
    tx_df = pd.read_parquet(out_dir / "cleaned_transactions.parquet")
    assert len(tx_df) == 5  # 4 + 2 - 1 dup = 5 rows

    # Customer commercial-ready excludes the promotional freebie:
    # 4 rows with customer ID: 5001, 5002, C5003, 5005. Row 5005 is freebie -> 3 remain
    cust_df = pd.read_parquet(out_dir / "customer_transactions.parquet")
    assert len(cust_df) == 4  # 5001, 5002, C5003, and 5004 is customer 33333 -> 4 commercial customer rows!
    assert (cust_df["price"] > 0).all()

    inv_df = pd.read_parquet(out_dir / "invoice_aggregates.parquet")
    assert len(inv_df) == 5  # 5 distinct invoices: 5001, 5002, C5003, 5005, 5004


@pytest.mark.full_data
def test_full_workbook_pipeline():
    """End-to-end verification on the full UCI Online Retail II raw workbook."""
    raw_path = Path("data/raw/online_retail_II.xlsx")
    if not raw_path.exists():
        pytest.skip("Full dataset workbook not found at data/raw/online_retail_II.xlsx")

    out_dir = Path("data/processed")
    rep_dir = Path("reports")

    exit_code = run_pipeline(
        input_path=raw_path,
        output_dir=out_dir,
        reports_dir=rep_dir,
        export_csv=True,
        engine="calamine",
    )

    assert exit_code == 0

    tx_parquet = out_dir / "cleaned_transactions.parquet"
    cust_parquet = out_dir / "customer_transactions.parquet"
    inv_parquet = out_dir / "invoice_aggregates.parquet"
    json_rep = rep_dir / "data_quality_audit.json"
    md_rep = rep_dir / "cleaning_and_reconciliation_summary.md"

    assert tx_parquet.exists()
    assert cust_parquet.exists()
    assert inv_parquet.exists()
    assert json_rep.exists()
    assert md_rep.exists()

    # Verify counts and invariants on actual full output
    tx_df = pd.read_parquet(tx_parquet)
    cust_df = pd.read_parquet(cust_parquet)
    inv_df = pd.read_parquet(inv_parquet)

    # 1. Row counts
    assert len(tx_df) == 1044848, f"Unexpected transactions count: {len(tx_df)}"
    assert len(cust_df) == 809491, f"Unexpected customer commercial-ready count: {len(cust_df)}"
    assert len(inv_df) == 53628, f"Unexpected invoices count: {len(inv_df)}"
    assert inv_df["customer_id"].nunique(dropna=True) == 5942

    # 2. Financial component exact reconciliation (tolerance £0.01)
    tx_prod = tx_df[tx_df["transaction_category"] == "standard_product_sale"]["line_total"].sum()
    tx_spec = tx_df[tx_df["transaction_category"] == "special_commercial_charge"]["line_total"].sum()
    tx_canc = tx_df[tx_df["transaction_category"] == "cancellation"]["line_total"].sum()
    tx_debt = tx_df[tx_df["transaction_category"] == "bad_debt_adjustment"]["line_total"].sum()
    tx_net = tx_df["line_total"].sum()

    assert np.isclose(inv_df["product_sales"].sum(), tx_prod, atol=0.01)
    assert np.isclose(inv_df["special_charges"].sum(), tx_spec, atol=0.01)
    assert np.isclose(inv_df["cancellation_value"].sum(), tx_canc, atol=0.01)
    assert np.isclose(inv_df["bad_debt_value"].sum(), tx_debt, atol=0.01)
    assert np.isclose(inv_df["net_value"].sum(), tx_net, atol=0.01)

    assert np.isclose(tx_prod, 19716362.61, atol=0.01)
    assert np.isclose(tx_spec, 806317.23, atol=0.01)
    assert np.isclose(tx_canc, -1465303.66, atol=0.01)
    assert np.isclose(tx_debt, -147614.08, atol=0.01)
    assert np.isclose(tx_net, 18909762.10, atol=0.01)

    # 3. Stock code audit deliverable verification
    stock_json = rep_dir / "special_stock_codes_audit.json"
    stock_md = rep_dir / "special_stock_codes_audit.md"
    assert stock_json.exists()
    assert stock_md.exists()

    # 4. RFM snapshot files and summary deliverables verification
    rfm_summary_json = rep_dir / "rfm_segmentation_summary.json"
    rfm_summary_md = rep_dir / "rfm_segmentation_summary.md"
    assert rfm_summary_json.exists()
    assert rfm_summary_md.exists()

    snap_dates = ["20101209", "20110610", "20110909", "20111209"]
    for s_date in snap_dates:
        snap_p = out_dir / f"rfm_snapshot_{s_date}.parquet"
        snap_c = out_dir / f"rfm_snapshot_{s_date}.csv"
        assert snap_p.exists(), f"Missing snapshot Parquet: {snap_p}"
        assert snap_c.exists(), f"Missing snapshot CSV: {snap_c}"

    # Verify RFM snapshot 2011-12-09 properties
    rfm_final = pd.read_parquet(out_dir / "rfm_snapshot_20111209.parquet")
    assert len(rfm_final) == 5853, f"Expected 5,853 qualifying customers, got {len(rfm_final)}"
    assert rfm_final["segment"].nunique() == 11
    assert (rfm_final["frequency"] >= 1).all()
    assert (rfm_final["recency_days"] >= 0).all()
    assert (rfm_final["customer_tenure_days"] >= rfm_final["recency_days"]).all()

    # Verify component reconciliation and conventional AOV metrics
    reconciled_net = (
        rfm_final["monetary_merchandise_sales"]
        + rfm_final["monetary_shipping"]
        + rfm_final["monetary_discounts"]
        + rfm_final["monetary_returns"]
        + rfm_final["monetary_manual_charges"]
    )
    assert np.allclose(rfm_final["net_commercial_spend"], reconciled_net, atol=0.01)

    reconciled_balance = rfm_final["net_commercial_spend"] + rfm_final["monetary_admin_settlements"]
    assert np.allclose(rfm_final["total_account_balance"], reconciled_balance, atol=0.01)

    # Conventional AOV must be strictly positive since qualifying gross sales > 0
    assert (rfm_final["avg_order_value"] > 0).all()
    assert np.allclose(
        rfm_final["avg_order_value"],
        rfm_final["qualifying_orders_gross_sales"] / rfm_final["frequency"],
        atol=0.01,
    )

    # Check unobserved future target at final history cutoff
    assert rfm_final["target_repeat_purchase_90d"].isna().all()
    assert not bool(rfm_final["is_target_window_observed"].iloc[0])

    # Check observed target rates on historical evaluation cutoffs
    rfm_c1 = pd.read_parquet(out_dir / "rfm_snapshot_20101209.parquet")
    rate_c1 = rfm_c1["target_repeat_purchase_90d"].mean()
    assert np.isclose(rate_c1, 0.3073, atol=0.005)

    rfm_c2 = pd.read_parquet(out_dir / "rfm_snapshot_20110610.parquet")
    rate_c2 = rfm_c2["target_repeat_purchase_90d"].mean()
    assert np.isclose(rate_c2, 0.3203, atol=0.005)

    rfm_c3 = pd.read_parquet(out_dir / "rfm_snapshot_20110909.parquet")
    rate_c3 = rfm_c3["target_repeat_purchase_90d"].mean()
    assert np.isclose(rate_c3, 0.4350, atol=0.005)
