"""Integration and end-to-end pipeline execution tests."""

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
    assert (out_dir / "invoice_aggregates.parquet").exists()
    assert (out_dir / "invoice_aggregates.csv").exists()
    assert (rep_dir / "data_quality_audit.json").exists()
    assert (rep_dir / "cleaning_and_reconciliation_summary.md").exists()

    # Reopen outputs and verify schemas and values
    tx_df = pd.read_parquet(out_dir / "cleaned_transactions.parquet")
    assert len(tx_df) == 4  # 3 + 2 - 1 dup = 4 rows

    inv_df = pd.read_parquet(out_dir / "invoice_aggregates.parquet")
    assert len(inv_df) == 4  # 4 distinct invoices: 5001, 5002, C5003, 5004


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
    inv_parquet = out_dir / "invoice_aggregates.parquet"
    json_rep = rep_dir / "data_quality_audit.json"
    md_rep = rep_dir / "cleaning_and_reconciliation_summary.md"

    assert tx_parquet.exists()
    assert inv_parquet.exists()
    assert json_rep.exists()
    assert md_rep.exists()

    # Verify counts and invariants on actual full output
    tx_df = pd.read_parquet(tx_parquet)
    inv_df = pd.read_parquet(inv_parquet)

    assert len(tx_df) == 1044848, f"Unexpected transactions count: {len(tx_df)}"
    assert len(inv_df) == 53628, f"Unexpected invoices count: {len(inv_df)}"
    assert inv_df["customer_id"].nunique(dropna=True) == 5942
