"""Workbook ingestion and schema validation for UCI Online Retail II."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when workbook loading or validation fails."""
    pass


@dataclass
class SheetData:
    """Container for ingested sheet data and metadata."""
    sheet_name: str
    data: pd.DataFrame
    row_count: int
    column_names: List[str]


def detect_excel_engine(preferred_engine: str = "calamine") -> str:
    """Select the best available Excel parsing engine."""
    if preferred_engine == "calamine":
        try:
            import python_calamine  # noqa: F401
            return "calamine"
        except ImportError:
            logger.info("python-calamine not available, falling back to openpyxl.")
            return "openpyxl"
    return preferred_engine


def load_workbook_sheets(
    workbook_path: Path,
    expected_sheets: Sequence[str] = ("Year 2009-2010", "Year 2010-2011"),
    required_columns: Sequence[str] = (
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    ),
    preferred_engine: str = "calamine",
) -> Dict[str, SheetData]:
    """Ingests both sheets from the Online Retail II workbook with validation and provenance.

    Parameters
    ----------
    workbook_path : Path
        Path to the Excel workbook.
    expected_sheets : Sequence[str]
        Expected sheet names.
    required_columns : Sequence[str]
        Required column names in each sheet.
    preferred_engine : str
        Preferred pandas Excel engine.

    Returns
    -------
    Dict[str, SheetData]
        Mapping of sheet name to SheetData container.

    Raises
    ------
    IngestionError
        If workbook does not exist, sheets are missing, or required columns are absent.
    """
    path = Path(workbook_path)
    if not path.exists():
        raise IngestionError(f"Workbook not found at: {path.resolve()}")
    if not path.is_file():
        raise IngestionError(f"Workbook path is not a file: {path.resolve()}")

    engine = detect_excel_engine(preferred_engine)
    logger.info("Opening workbook '%s' using engine '%s'...", path, engine)

    try:
        excel_file = pd.ExcelFile(path, engine=engine)
    except Exception as exc:
        raise IngestionError(f"Failed to open Excel workbook at {path}: {exc}") from exc

    available_sheets = excel_file.sheet_names
    missing_sheets = [s for s in expected_sheets if s not in available_sheets]
    if missing_sheets:
        raise IngestionError(
            f"Workbook is missing expected sheet(s): {missing_sheets}. "
            f"Available sheets: {available_sheets}"
        )

    results: Dict[str, SheetData] = {}
    for sheet_name in expected_sheets:
        logger.info("Reading sheet: '%s'...", sheet_name)
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
        except Exception as exc:
            raise IngestionError(f"Failed to read sheet '{sheet_name}': {exc}") from exc

        # Validate columns
        actual_cols = list(df.columns)
        missing_cols = [c for c in required_columns if c not in actual_cols]
        if missing_cols:
            raise IngestionError(
                f"Sheet '{sheet_name}' is missing required column(s): {missing_cols}. "
                f"Present columns: {actual_cols}"
            )

        # Attach provenance: sheet name and original 1-indexed row number in Excel
        # In Excel, row 1 is header, so row 2 is the first data row (index 0 + 2)
        df["source_sheet"] = sheet_name
        df["source_row_num"] = df.index + 2

        results[sheet_name] = SheetData(
            sheet_name=sheet_name,
            data=df,
            row_count=len(df),
            column_names=actual_cols,
        )
        logger.info(
            "Sheet '%s' ingested successfully: %d rows, %d columns.",
            sheet_name,
            len(df),
            len(actual_cols),
        )

    return results
