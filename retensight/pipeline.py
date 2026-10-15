"""Pipeline orchestration for RetenSight data ingestion and cleaning."""

import argparse
import logging
from pathlib import Path
import sys
import time
from typing import Optional

import pandas as pd

from retensight.aggregation import build_invoice_aggregates
from retensight.audit import generate_pipeline_audit, save_audit_reports
from retensight.cleaning import clean_and_classify_transactions
from retensight.config import PipelineConfig
from retensight.deduplication import resolve_cross_sheet_duplicates
from retensight.ingestion import IngestionError, load_workbook_sheets
from retensight.rfm import (
    build_all_rfm_snapshots,
    save_rfm_summary_reports,
    summarize_rfm_snapshots,
)
from retensight.stock_code_audit import (
    audit_special_stock_codes,
    save_stock_code_audit_reports,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("retensight.pipeline")


def run_pipeline(
    input_path: Path = Path("data/raw/online_retail_II.xlsx"),
    output_dir: Path = Path("data/processed"),
    reports_dir: Path = Path("reports"),
    export_csv: bool = True,
    engine: str = "calamine",
) -> int:
    """Executes the full ingestion, deduplication, cleaning, aggregation,

    and audit pipeline.

    Parameters
    ----------
    input_path : Path
        Path to the UCI Online Retail II Excel workbook.
    output_dir : Path
        Directory to save processed datasets (Parquet / CSV).
    reports_dir : Path
        Directory to save audit reports (JSON / Markdown).
    export_csv : bool
        Whether to export CSV files alongside Parquet.
    engine : str
        Excel reader engine ('calamine' or 'openpyxl').

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure).
    """
    start_time = time.time()
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    reports_dir = Path(reports_dir)

    logger.info("==================================================")
    logger.info("RetenSight Data Pipeline Execution Started")
    logger.info("Input workbook : %s", input_path.resolve())
    logger.info("Output directory: %s", output_dir.resolve())
    logger.info("Reports directory: %s", reports_dir.resolve())
    logger.info("==================================================")

    # 1. Ingestion
    try:
        sheets_data = load_workbook_sheets(
            workbook_path=input_path,
            preferred_engine=engine,
        )
    except IngestionError as exc:
        logger.error("Ingestion failed: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Unexpected error during ingestion: %s", exc)
        return 1

    sheet1 = sheets_data["Year 2009-2010"].data
    sheet2 = sheets_data["Year 2010-2011"].data

    # 2. Cross-sheet exact duplicate resolution
    try:
        combined_raw, dedup_audit = resolve_cross_sheet_duplicates(
            sheet1_df=sheet1,
            sheet2_df=sheet2,
            sheet1_name="Year 2009-2010",
            sheet2_name="Year 2010-2011",
        )
    except Exception as exc:
        logger.exception("Cross-sheet deduplication failed: %s", exc)
        return 1

    # 3. Normalization and Cleaning
    try:
        cleaned_tx = clean_and_classify_transactions(combined_raw)
    except Exception as exc:
        logger.exception("Data cleaning and classification failed: %s", exc)
        return 1

    # 4. Invoice-level Aggregation
    try:
        invoices_df = build_invoice_aggregates(cleaned_tx)
    except Exception as exc:
        logger.exception("Invoice aggregation failed: %s", exc)
        return 1

    # 5. Pipeline Audit & Invariant Checks
    try:
        audit_dict = generate_pipeline_audit(
            dedup_audit=dedup_audit,
            transactions_df=cleaned_tx,
            invoices_df=invoices_df,
        )
    except Exception as exc:
        logger.exception("Audit generation or reconciliation invariant check failed: %s", exc)
        return 1

    # 6. Special Stock Code Audit
    try:
        stock_audit_dict = audit_special_stock_codes(cleaned_tx)
    except Exception as exc:
        logger.exception("Special stock code audit failed: %s", exc)
        return 1

    # 7. Customer RFM Feature Snapshots across Chronological Cutoffs
    try:
        rfm_snapshots = build_all_rfm_snapshots(invoices_df=invoices_df)
        rfm_summary = summarize_rfm_snapshots(rfm_snapshots, invoices_df=invoices_df)
    except Exception as exc:
        logger.exception("Customer RFM snapshot generation failed: %s", exc)
        return 1

    # 8. Save Processed Outputs
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Primary Parquet outputs
        tx_parquet_path = output_dir / "cleaned_transactions.parquet"
        inv_parquet_path = output_dir / "invoice_aggregates.parquet"
        cust_parquet_path = output_dir / "customer_transactions.parquet"

        logger.info("Writing Parquet files to '%s'...", output_dir)
        cleaned_tx.to_parquet(tx_parquet_path, index=False)
        invoices_df.to_parquet(inv_parquet_path, index=False)

        # Filtered customer commercial-ready dataset (model-ready: sales, charges, cancellations; excludes promotional freebies)
        cust_tx = cleaned_tx[cleaned_tx["is_commercial_customer_ready"]].copy()
        cust_tx.to_parquet(cust_parquet_path, index=False)

        # Save RFM snapshots (Parquet and CSV)
        all_rfm_records = []
        for date_label, snapshot_df in rfm_snapshots.items():
            compact_date = date_label.replace("-", "")
            snap_parquet = output_dir / f"rfm_snapshot_{compact_date}.parquet"
            snapshot_df.to_parquet(snap_parquet, index=False)
            if export_csv:
                snap_csv = output_dir / f"rfm_snapshot_{compact_date}.csv"
                snapshot_df.to_csv(snap_csv, index=False)
            all_rfm_records.append(snapshot_df)

        # Combined multi-cutoff RFM dataset
        combined_rfm = pd.concat(all_rfm_records, ignore_index=True)
        combined_rfm.to_parquet(output_dir / "rfm_summary_all_cutoffs.parquet", index=False)
        if export_csv:
            combined_rfm.to_csv(output_dir / "rfm_summary_all_cutoffs.csv", index=False)

        # CSV exports if requested
        if export_csv:
            logger.info("Writing CSV files to '%s'...", output_dir)
            inv_csv_path = output_dir / "invoice_aggregates.csv"
            invoices_df.to_csv(inv_csv_path, index=False)

            # Also export customer transactions sample for preview
            cust_csv_path = output_dir / "customer_transactions_sample.csv"
            cust_tx.head(10000).to_csv(cust_csv_path, index=False)

        # Save audit reports
        json_report_path = reports_dir / "data_quality_audit.json"
        md_report_path = reports_dir / "cleaning_and_reconciliation_summary.md"
        save_audit_reports(audit_dict, json_report_path, md_report_path)

        # Save stock code audit reports
        save_stock_code_audit_reports(
            audit_dict=stock_audit_dict,
            json_path=reports_dir / "special_stock_codes_audit.json",
            md_path=reports_dir / "special_stock_codes_audit.md",
        )

        # Save RFM summary reports
        save_rfm_summary_reports(
            summary_dict=rfm_summary,
            json_path=reports_dir / "rfm_segmentation_summary.json",
            md_path=reports_dir / "rfm_segmentation_summary.md",
        )

        # Also store copies in data/audit if data directory exists
        data_audit_dir = Path("data/audit")
        if data_audit_dir.parent.exists():
            save_audit_reports(
                audit_dict,
                data_audit_dir / "data_quality_audit.json",
                data_audit_dir / "cleaning_and_reconciliation_summary.md",
            )
            save_stock_code_audit_reports(
                stock_audit_dict,
                data_audit_dir / "special_stock_codes_audit.json",
                data_audit_dir / "special_stock_codes_audit.md",
            )
            save_rfm_summary_reports(
                rfm_summary,
                data_audit_dir / "rfm_segmentation_summary.json",
                data_audit_dir / "rfm_segmentation_summary.md",
            )

    except Exception as exc:
        logger.exception("Failed to export pipeline deliverables: %s", exc)
        return 1

    elapsed = time.time() - start_time
    logger.info("==================================================")
    logger.info("RetenSight Pipeline Finished Successfully in %.2f seconds", elapsed)
    logger.info("Retained Transactions       : %d", len(cleaned_tx))
    logger.info("Customer Model-Ready Rows   : %d", len(cust_tx))
    logger.info("Unique Invoices             : %d", len(invoices_df))
    logger.info("Distinct Customers          : %d", invoices_df["customer_id"].nunique(dropna=True))
    logger.info("RFM Snapshots Generated     : %d cutoffs (%s)", len(rfm_snapshots), ", ".join(rfm_snapshots.keys()))
    logger.info("Gross Product Sales         : £%s", f"{audit_dict['financial_reconciliation']['gross_product_sales_gbp']:,.2f}")
    logger.info("Special Commercial Charges  : £%s", f"{audit_dict['financial_reconciliation']['special_commercial_charges_gbp']:,.2f}")
    logger.info("Total Gross Sales           : £%s", f"{audit_dict['financial_reconciliation']['gross_sales_gbp']:,.2f}")
    logger.info("Cancellations / Refunds     : £%s", f"{audit_dict['financial_reconciliation']['cancellations_value_gbp']:,.2f}")
    logger.info("Net Commercial Value        : £%s", f"{audit_dict['financial_reconciliation']['net_commercial_value_gbp']:,.2f}")
    logger.info("Bad Debt Adjustments        : £%s", f"{audit_dict['financial_reconciliation']['bad_debt_adjustments_gbp']:,.2f}")
    logger.info("All Transactions Net Value  : £%s", f"{audit_dict['financial_reconciliation']['all_transactions_net_value_gbp']:,.2f}")
    logger.info("==================================================")

    return 0


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="RetenSight E-commerce CRM Data Cleaning and Aggregation Pipeline"
    )
    parser.add_argument(
        "--input-path",
        "-i",
        type=Path,
        default=Path("data/raw/online_retail_II.xlsx"),
        help="Path to UCI Online Retail II raw workbook (default: data/raw/online_retail_II.xlsx)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for processed data (default: data/processed)",
    )
    parser.add_argument(
        "--reports-dir",
        "-r",
        type=Path,
        default=Path("reports"),
        help="Output directory for audit reports (default: reports)",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Disable CSV export (Parquet only)",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="calamine",
        choices=["calamine", "openpyxl"],
        help="Excel reading engine (default: calamine)",
    )

    args = parser.parse_args()

    exit_code = run_pipeline(
        input_path=args.input_path,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        export_csv=not args.no_csv,
        engine=args.engine,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
