"""Configuration definitions and defaults for the RetenSight data pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration settings for pipeline execution."""

    # File paths
    input_workbook_path: Path = Path("data/raw/online_retail_II.xlsx")
    output_dir: Path = Path("data/processed")
    reports_dir: Path = Path("reports")

    # Sheet definitions
    expected_sheets: Sequence[str] = ("Year 2009-2010", "Year 2010-2011")

    # Column mappings
    raw_columns: Sequence[str] = (
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    )

    # Special stock codes representing administrative or service charges
    special_stock_codes: Sequence[str] = (
        "POST",
        "D",
        "M",
        "BANK CHARGES",
        "AMAZONFEE",
        "DOT",
        "CRUK",
        "S",
        "ADJUST",
        "ADJUST2",
        "B",
        "TEST",
        "PADS",
        "GIFT",
    )

    # Output options
    export_csv: bool = True
    export_parquet: bool = True

    # Performance
    excel_engine: str = "calamine"  # Falls back to openpyxl if unavailable
