"""Cross-sheet exact duplicate detection and resolution.

This module resolves the known date overlap between Sheet 1 ('Year 2009-2010')
and Sheet 2 ('Year 2010-2011') using strict 1-to-1 matching of identical rows
across sheets only, preserving legitimate same-sheet repeated purchases.
"""

from dataclasses import dataclass
import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationAudit:
    """Audit metrics for cross-sheet duplicate removal."""
    sheet1_name: str
    sheet2_name: str
    sheet1_rows_read: int
    sheet2_rows_read: int
    total_raw_rows: int
    cross_sheet_duplicates_removed: int
    retained_rows: int
    sheet1_rows_in_same_sheet_dups: int
    sheet2_rows_in_same_sheet_dups_pre: int
    overlap_window_start: Optional[str]
    overlap_window_end: Optional[str]


def resolve_cross_sheet_duplicates(
    sheet1_df: pd.DataFrame,
    sheet2_df: pd.DataFrame,
    comparison_columns: Sequence[str] = (
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    ),
    sheet1_name: str = "Year 2009-2010",
    sheet2_name: str = "Year 2010-2011",
) -> Tuple[pd.DataFrame, DeduplicationAudit]:
    """Identifies and removes exact 1-to-1 cross-sheet duplicate copies from sheet 2.

    Parameters
    ----------
    sheet1_df : pd.DataFrame
        Data from first sheet ('Year 2009-2010').
    sheet2_df : pd.DataFrame
        Data from second sheet ('Year 2010-2011').
    comparison_columns : Sequence[str]
        Columns that define row identity.
    sheet1_name : str
        Name of sheet 1.
    sheet2_name : str
        Name of sheet 2.

    Returns
    -------
    Tuple[pd.DataFrame, DeduplicationAudit]
        - Combined DataFrame with cross-sheet duplicate copies removed from sheet 2.
        - Detailed DeduplicationAudit record.
    """
    comp_cols = list(comparison_columns)
    s1_count = len(sheet1_df)
    s2_count = len(sheet2_df)
    total_raw = s1_count + s2_count

    logger.info(
        "Starting cross-sheet deduplication: %s (%d rows) vs %s (%d rows)...",
        sheet1_name,
        s1_count,
        sheet2_name,
        s2_count,
    )

    # 1. Measure same-sheet duplicates prior to cross-sheet resolution
    # (These must be preserved, not dropped!)
    s1_same_sheet_dup_count = int(sheet1_df.duplicated(subset=comp_cols, keep=False).sum())
    s2_same_sheet_dup_count_pre = int(sheet2_df.duplicated(subset=comp_cols, keep=False).sum())
    logger.info(
        "Same-sheet duplicate rows before resolution: %s=%d, %s=%d",
        sheet1_name,
        s1_same_sheet_dup_count,
        sheet2_name,
        s2_same_sheet_dup_count_pre,
    )

    # 2. Compute within-sheet occurrence multiplicity index (1, 2, 3...)
    # dropna=False ensures that rows with NaN Customer ID or Description are grouped together
    df1 = sheet1_df.copy()
    df2 = sheet2_df.copy()
    df1["_occ_id"] = df1.groupby(comp_cols, dropna=False).cumcount() + 1
    df2["_occ_id"] = df2.groupby(comp_cols, dropna=False).cumcount() + 1

    # Attach internal row identifier to df2 to isolate matched duplicate records
    df2["_internal_id"] = np.arange(len(df2))

    # 3. Exact 1-to-1 matching across sheets
    # A row in df2 matches df1 if all comp_cols AND _occ_id are identical
    match_keys = comp_cols + ["_occ_id"]
    matched = pd.merge(
        df2[["_internal_id"] + match_keys],
        df1[match_keys],
        on=match_keys,
        how="inner",
    )

    duplicate_internal_ids = set(matched["_internal_id"])
    num_duplicates_removed = len(duplicate_internal_ids)
    logger.info(
        "Found %d exact 1-to-1 cross-sheet duplicate rows in %s.",
        num_duplicates_removed,
        sheet2_name,
    )

    # Determine overlap date window of matched rows
    if num_duplicates_removed > 0:
        matched_dates = pd.to_datetime(matched["InvoiceDate"])
        overlap_start = str(matched_dates.min())
        overlap_end = str(matched_dates.max())
    else:
        overlap_start = None
        overlap_end = None

    # 4. Filter out duplicate occurrences from sheet 2
    df2_retained = df2[~df2["_internal_id"].isin(duplicate_internal_ids)].copy()

    # Clean up internal columns
    df1 = df1.drop(columns=["_occ_id"])
    df2_retained = df2_retained.drop(columns=["_occ_id", "_internal_id"])

    # 5. Concatenate sheet 1 and retained sheet 2 rows
    combined_df = pd.concat([df1, df2_retained], ignore_index=True)
    retained_count = len(combined_df)

    # Verify reconciliation invariant
    assert retained_count == total_raw - num_duplicates_removed, (
        f"Deduplication row count mismatch: {retained_count} != "
        f"{total_raw} - {num_duplicates_removed}"
    )

    audit = DeduplicationAudit(
        sheet1_name=sheet1_name,
        sheet2_name=sheet2_name,
        sheet1_rows_read=s1_count,
        sheet2_rows_read=s2_count,
        total_raw_rows=total_raw,
        cross_sheet_duplicates_removed=num_duplicates_removed,
        retained_rows=retained_count,
        sheet1_rows_in_same_sheet_dups=s1_same_sheet_dup_count,
        sheet2_rows_in_same_sheet_dups_pre=s2_same_sheet_dup_count_pre,
        overlap_window_start=overlap_start,
        overlap_window_end=overlap_end,
    )

    return combined_df, audit
