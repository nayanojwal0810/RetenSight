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
    # Note: PADS is physical cushion merchandise and is excluded from special administrative codes.
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
        "GIFT",
    )

    # Sub-classification taxonomy for customer commercial spend vs administrative entries
    administrative_stock_codes: Sequence[str] = (
        "CRUK",
        "ADJUST",
        "ADJUST2",
        "BANK CHARGES",
    )
    shipping_stock_codes: Sequence[str] = (
        "POST",
        "DOT",
    )
    discount_stock_codes: Sequence[str] = (
        "D",
    )
    manual_stock_codes: Sequence[str] = (
        "M",
    )

    # Output options
    export_csv: bool = True
    export_parquet: bool = True

    # Performance
    excel_engine: str = "calamine"  # Falls back to openpyxl if unavailable

    # RFM snapshot evaluation cutoffs (chronological evaluation windows with full 90-day observation)
    evaluation_cutoffs: Sequence[str] = (
        "2010-12-09 23:59:59",  # Cutoff 1: 12 months history (target: 2010-12-10 to 2011-03-09 23:59:59)
        "2011-06-10 23:59:59",  # Cutoff 2: 18 months history (target: 2011-06-11 to 2011-09-08 23:59:59)
        "2011-09-09 23:59:59",  # Cutoff 3: 21 months history (target: 2011-09-10 to 2011-12-08 23:59:59)
    )
    full_history_cutoff: str = "2011-12-09 12:50:00"  # Complete 24 months dataset end (target unobserved)
    forward_target_window_days: int = 90
