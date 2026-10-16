"""Data loading, validation, and filtering layer for the RetenSight dashboard.

Loads only verified aggregate report artifacts from the reports directory,
enforcing strict schema validation and invariant checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


REQUIRED_REPORT_FILES = [
    "data_quality_audit.json",
    "rfm_segmentation_summary.json",
    "crm_segment_decision_table.csv",
    "repeat_purchase_model_metrics.csv",
    "crm_queue_policy_comparison.csv",
    "repeat_purchase_model_config.json",
]


class DashboardDataError(Exception):
    """Raised when an artifact is missing or fails schema validation."""


def validate_reports_directory(reports_dir: Path | str) -> Path:
    """Verifies that the reports directory exists and contains all required artifacts."""
    path = Path(reports_dir)
    if not path.is_dir():
        raise DashboardDataError(f"Reports directory does not exist: {path.resolve()}")

    missing = [f for f in REQUIRED_REPORT_FILES if not (path / f).exists()]
    if missing:
        raise DashboardDataError(f"Missing required report artifacts in {path}: {', '.join(missing)}")

    return path


def load_data_quality_audit(reports_dir: Path | str) -> Dict[str, Any]:
    """Loads and validates the data quality and reconciliation audit JSON."""
    path = Path(reports_dir) / "data_quality_audit.json"
    if not path.exists():
        raise DashboardDataError(f"Missing data quality audit: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception as exc:
        raise DashboardDataError(f"Malformed JSON in data quality audit {path}: {exc}") from exc

    required_sections = ["ingestion", "deduplication", "transactions_breakdown", "invoice_breakdown", "financial_reconciliation"]
    for sec in required_sections:
        if sec not in data:
            raise DashboardDataError(f"Data quality audit missing required section '{sec}'")

    return data


def load_rfm_summary(reports_dir: Path | str) -> Dict[str, Any]:
    """Loads and validates the RFM segmentation summary JSON."""
    path = Path(reports_dir) / "rfm_segmentation_summary.json"
    if not path.exists():
        raise DashboardDataError(f"Missing RFM summary: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception as exc:
        raise DashboardDataError(f"Malformed JSON in RFM summary {path}: {exc}") from exc

    if "cutoffs" not in data:
        raise DashboardDataError("RFM summary missing 'cutoffs' dictionary")

    expected_cutoffs = ["2010-12-09", "2011-06-10", "2011-09-09", "2011-12-09"]
    for cutoff in expected_cutoffs:
        if cutoff not in data["cutoffs"]:
            raise DashboardDataError(f"RFM summary missing expected cutoff '{cutoff}'")

    return data


def load_segment_decision_table(reports_dir: Path | str) -> pd.DataFrame:
    """Loads and validates the 125-cell CRM segment decision table CSV."""
    path = Path(reports_dir) / "crm_segment_decision_table.csv"
    if not path.exists():
        raise DashboardDataError(f"Missing CRM segment decision table: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DashboardDataError(f"Error reading CRM decision table {path}: {exc}") from exc

    required_cols = {"r_score", "f_score", "m_score", "segment", "spend_condition", "business_rationale", "core_crm_action"}
    if not required_cols.issubset(df.columns):
        raise DashboardDataError(f"CRM decision table missing columns: {required_cols - set(df.columns)}")

    if len(df) < 125:
        raise DashboardDataError(f"CRM decision table incomplete: expected >=125 rows, got {len(df)}")

    return df


def load_model_metrics(reports_dir: Path | str) -> pd.DataFrame:
    """Loads and validates repeat-purchase propensity model metrics CSV."""
    path = Path(reports_dir) / "repeat_purchase_model_metrics.csv"
    if not path.exists():
        raise DashboardDataError(f"Missing model metrics: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DashboardDataError(f"Error reading model metrics {path}: {exc}") from exc

    required_cols = {
        "model_name", "split_name", "snapshot_date", "sample_count",
        "positive_count", "negative_count", "base_rate", "roc_auc",
        "average_precision", "brier_score"
    }
    if not required_cols.issubset(df.columns):
        raise DashboardDataError(f"Model metrics missing columns: {required_cols - set(df.columns)}")

    expected_splits = {"Validation", "Retrospective Temporal Evaluation"}
    if not expected_splits.issubset(set(df["split_name"])):
        raise DashboardDataError(f"Model metrics missing expected splits: {expected_splits - set(df['split_name'])}")

    return df


def load_crm_policy_comparison(reports_dir: Path | str) -> pd.DataFrame:
    """Loads and validates CRM queue outreach policy comparison CSV."""
    path = Path(reports_dir) / "crm_queue_policy_comparison.csv"
    if not path.exists():
        raise DashboardDataError(f"Missing CRM policy comparison: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DashboardDataError(f"Error reading CRM policy comparison {path}: {exc}") from exc

    required_cols = {
        "evaluation_split", "model_name", "outreach_capacity", "outreach_capacity_fraction",
        "selected_count", "policy", "selected_non_repeaters", "selected_non_repeat_rate",
        "share_of_all_non_repeaters_captured", "historical_commercial_value_gbp",
        "share_of_cohort_commercial_value"
    }
    if not required_cols.issubset(df.columns):
        raise DashboardDataError(f"CRM policy comparison missing columns: {required_cols - set(df.columns)}")

    if len(df) != 64:
        raise DashboardDataError(f"Expected exactly 64 rows in CRM policy comparison, got {len(df)}")

    return df


def load_model_config(reports_dir: Path | str) -> Dict[str, Any]:
    """Loads and validates repeat-purchase model configuration JSON."""
    path = Path(reports_dir) / "repeat_purchase_model_config.json"
    if not path.exists():
        raise DashboardDataError(f"Missing model config: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception as exc:
        raise DashboardDataError(f"Malformed JSON in model config {path}: {exc}") from exc

    if "recommended_default_model" not in data or "challenger_model" not in data:
        raise DashboardDataError("Model config missing model recommendation designations")

    if data["recommended_default_model"] != "RFM Baseline":
        raise DashboardDataError(f"Expected default model 'RFM Baseline', found '{data['recommended_default_model']}'")

    return data


def filter_crm_policies(
    df: pd.DataFrame,
    evaluation_split: str,
    model_name: str,
    outreach_capacity: str,
    policy: Optional[str] = None,
) -> pd.DataFrame:
    """Filters the CRM policy comparison table for given selection criteria."""
    filtered = df[
        (df["evaluation_split"] == evaluation_split)
        & (df["model_name"] == model_name)
        & (df["outreach_capacity"] == outreach_capacity)
    ].copy()

    if policy is not None and policy != "All Policies":
        filtered = filtered[filtered["policy"] == policy]

    return filtered


def get_segment_strategy_summary(decision_df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicates the decision table to provide one distinct business rationale

    and CRM action per segment.
    """
    summary = decision_df[["segment", "business_rationale", "core_crm_action"]].drop_duplicates(subset=["segment"])
    return summary.sort_values("segment").reset_index(drop=True)
