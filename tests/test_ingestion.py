"""Unit tests for workbook ingestion and schema validation."""

from pathlib import Path
import pandas as pd
import pytest

from retensight.ingestion import IngestionError, load_workbook_sheets


def test_missing_workbook_raises_error(tmp_path):
    """Verifies that non-existent workbook raises IngestionError."""
    fake_path = tmp_path / "non_existent.xlsx"
    with pytest.raises(IngestionError, match="Workbook not found"):
        load_workbook_sheets(fake_path)


def test_missing_sheets_raises_error(tmp_path):
    """Verifies that workbook missing an expected sheet raises IngestionError."""
    test_excel = tmp_path / "test_sheets.xlsx"
    with pd.ExcelWriter(test_excel, engine="openpyxl") as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="Sheet1", index=False)

    with pytest.raises(IngestionError, match="missing expected sheet"):
        load_workbook_sheets(test_excel, expected_sheets=["Year 2009-2010", "Year 2010-2011"])


def test_missing_columns_raises_error(tmp_path):
    """Verifies that sheet missing a required column raises IngestionError."""
    test_excel = tmp_path / "test_cols.xlsx"
    with pd.ExcelWriter(test_excel, engine="openpyxl") as writer:
        pd.DataFrame({"Invoice": [1], "StockCode": ["A"]}).to_excel(
            writer, sheet_name="Year 2009-2010", index=False
        )
        pd.DataFrame({"Invoice": [1], "StockCode": ["A"]}).to_excel(
            writer, sheet_name="Year 2010-2011", index=False
        )

    with pytest.raises(IngestionError, match="missing required column"):
        load_workbook_sheets(
            test_excel,
            expected_sheets=["Year 2009-2010", "Year 2010-2011"],
            required_columns=["Invoice", "StockCode", "Description"],
        )


def test_successful_ingestion_with_provenance(tmp_path):
    """Verifies successful loading of valid workbook with attached provenance."""
    test_excel = tmp_path / "valid_wb.xlsx"
    cols = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    row_data = [(101, "A1", "Item", 1, "2010-01-01", 10.0, 12345, "UK")]

    with pd.ExcelWriter(test_excel, engine="openpyxl") as writer:
        pd.DataFrame(row_data, columns=cols).to_excel(writer, sheet_name="Year 2009-2010", index=False)
        pd.DataFrame(row_data, columns=cols).to_excel(writer, sheet_name="Year 2010-2011", index=False)

    sheets = load_workbook_sheets(test_excel, expected_sheets=["Year 2009-2010", "Year 2010-2011"])

    assert "Year 2009-2010" in sheets
    assert "Year 2010-2011" in sheets

    s1_df = sheets["Year 2009-2010"].data
    assert "source_sheet" in s1_df.columns
    assert "source_row_num" in s1_df.columns
    assert s1_df["source_sheet"].iloc[0] == "Year 2009-2010"
    assert s1_df["source_row_num"].iloc[0] == 2
