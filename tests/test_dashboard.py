"""Automated unit and integration tests for the RetenSight Streamlit dashboard data layer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pytest

from retensight.dashboard_data import (
    DashboardDataError,
    filter_crm_policies,
    get_segment_strategy_summary,
    load_crm_policy_comparison,
    load_data_quality_audit,
    load_model_config,
    load_model_metrics,
    load_rfm_summary,
    load_segment_decision_table,
    validate_reports_directory,
)


REPORTS_DIR = Path("reports")


def test_validate_reports_directory_success() -> None:
    """Verifies that validate_reports_directory succeeds when all required files are present."""
    p = validate_reports_directory(REPORTS_DIR)
    assert p == REPORTS_DIR


def test_validate_reports_directory_missing_files(tmp_path: Path) -> None:
    """Verifies that validate_reports_directory raises DashboardDataError for missing files."""
    with pytest.raises(DashboardDataError, match="Missing required report artifacts"):
        validate_reports_directory(tmp_path)


def test_load_data_quality_audit_schema_and_invariants() -> None:
    """Verifies schema and critical financial figures in data_quality_audit.json."""
    audit = load_data_quality_audit(REPORTS_DIR)
    assert "ingestion" in audit
    assert "deduplication" in audit
    assert "transactions_breakdown" in audit
    assert "invoice_breakdown" in audit
    assert "financial_reconciliation" in audit

    # Key verified figures
    inv = audit["invoice_breakdown"]
    assert inv["distinct_valid_customers"] == 5942
    assert inv["total_unique_invoices"] == 53628

    fin = audit["financial_reconciliation"]
    assert np.isclose(fin["gross_sales_gbp"], 20522679.84, atol=0.01)
    assert np.isclose(fin["net_commercial_value_gbp"], 19057376.18, atol=0.01)
    assert np.isclose(fin["invoice_net_revenue_sum_gbp"], 18909762.10, atol=0.01)
    assert np.isclose(fin["revenue_discrepancy_gbp"], 0.0, atol=0.001)


def test_load_rfm_summary_schema_and_cutoffs() -> None:
    """Verifies RFM summary cutoffs, eligible counts, and repeat rates."""
    rfm = load_rfm_summary(REPORTS_DIR)
    assert "cutoffs" in rfm
    cutoffs = rfm["cutoffs"]

    # Invariants across all 4 snapshots
    assert set(cutoffs.keys()) == {"2010-12-09", "2011-06-10", "2011-09-09", "2011-12-09"}

    c1 = cutoffs["2010-12-09"]
    assert c1["eligible_customers"] == 4286
    assert c1["repeat_purchasers_90d"] == 1317
    assert np.isclose(c1["repeat_purchase_rate_pct"], 30.73, atol=0.01)

    c2 = cutoffs["2011-06-10"]  # Validation
    assert c2["eligible_customers"] == 4952
    assert c2["repeat_purchasers_90d"] == 1586
    assert np.isclose(c2["repeat_purchase_rate_pct"], 32.03, atol=0.01)

    c3 = cutoffs["2011-09-09"]  # Retrospective evaluation
    assert c3["eligible_customers"] == 5257
    assert c3["repeat_purchasers_90d"] == 2287
    assert np.isclose(c3["repeat_purchase_rate_pct"], 43.50, atol=0.01)

    c4 = cutoffs["2011-12-09"]  # Unobserved production
    assert c4["eligible_customers"] == 5853
    assert c4["repeat_purchasers_90d"] is None
    assert c4["is_target_window_observed"] is False


def test_load_segment_decision_table_and_strategy_summary() -> None:
    """Verifies segment decision table schema and distinct segment strategy summary."""
    df = load_segment_decision_table(REPORTS_DIR)
    assert len(df) >= 125
    expected_cols = {"r_score", "f_score", "m_score", "segment", "spend_condition", "business_rationale", "core_crm_action"}
    assert expected_cols.issubset(set(df.columns))

    summary = get_segment_strategy_summary(df)
    assert len(summary) == 11
    assert "Champions" in summary["segment"].values
    assert "At Risk" in summary["segment"].values
    assert "Lost" in summary["segment"].values


def test_load_model_metrics_schema_and_values() -> None:
    """Verifies repeat purchase model metrics table contents."""
    df = load_model_metrics(REPORTS_DIR)
    assert len(df) == 4
    assert set(df["model_name"]) == {"RFM Baseline", "Expanded Model"}
    assert set(df["split_name"]) == {"Validation", "Retrospective Temporal Evaluation"}

    # Validation split checks
    val_rfm = df[(df["model_name"] == "RFM Baseline") & (df["split_name"] == "Validation")].iloc[0]
    assert np.isclose(val_rfm["roc_auc"], 0.8026, atol=0.001)
    assert np.isclose(val_rfm["brier_score"], 0.1594, atol=0.001)

    val_exp = df[(df["model_name"] == "Expanded Model") & (df["split_name"] == "Validation")].iloc[0]
    assert np.isclose(val_exp["roc_auc"], 0.8079, atol=0.001)
    assert np.isclose(val_exp["brier_score"], 0.1583, atol=0.001)


def test_crm_policy_comparison_filtering_and_record_matching() -> None:
    """Verifies CRM queue policy comparison schema, exact 64-row size, and precise filtering."""
    df = load_crm_policy_comparison(REPORTS_DIR)
    assert len(df) == 64

    # Test filtering at 10% capacity in Validation for RFM Baseline
    val_10 = filter_crm_policies(
        df,
        evaluation_split="Validation",
        model_name="RFM Baseline",
        outreach_capacity="10%",
    )
    assert len(val_10) == 4
    assert set(val_10["policy"]) == {
        "Risk-first", "Value-aware", "Hybrid", "Random baseline (analytical)"
    }

    # Verify exact figures for Risk-first at 10% capacity in Validation
    risk_row = val_10[val_10["policy"] == "Risk-first"].iloc[0]
    assert risk_row["selected_count"] == 495
    assert np.isclose(risk_row["selected_non_repeaters"], 470.0)
    assert np.isclose(risk_row["selected_non_repeat_rate"], 0.9495, atol=0.0001)
    assert np.isclose(risk_row["share_of_all_non_repeaters_captured"], 0.1396, atol=0.0001)

    # Verify exact figures for Value-aware at 10% capacity in Validation
    val_row = val_10[val_10["policy"] == "Value-aware"].iloc[0]
    assert val_row["selected_count"] == 495
    assert np.isclose(val_row["selected_non_repeaters"], 236.0)
    assert np.isclose(val_row["selected_non_repeat_rate"], 0.4768, atol=0.0001)
    assert np.isclose(val_row["historical_commercial_value_gbp"], 4736269.92, atol=1.0)
    assert np.isclose(val_row["share_of_cohort_commercial_value"], 0.4129, atol=0.001)


def test_load_model_config_default_recommendation() -> None:
    """Verifies that repeat_purchase_model_config.json designates RFM Baseline as default."""
    cfg = load_model_config(REPORTS_DIR)
    assert cfg["recommended_default_model"] == "RFM Baseline"
    assert cfg["challenger_model"] == "Expanded Model"
    assert "selection_rationale" in cfg
    assert len(cfg["feature_sets"]["rfm_baseline"]) == 3
    assert len(cfg["feature_sets"]["expanded_features"]) == 16


def test_malformed_artifact_handling(tmp_path: Path) -> None:
    """Verifies that malformed JSON or corrupted CSV raises DashboardDataError."""
    # Write invalid JSON
    bad_json = tmp_path / "data_quality_audit.json"
    bad_json.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(DashboardDataError, match="Malformed JSON"):
        load_data_quality_audit(tmp_path)

    # Write CSV missing required columns
    bad_csv = tmp_path / "crm_queue_policy_comparison.csv"
    pd.DataFrame({"dummy": [1, 2]}).to_csv(bad_csv, index=False)
    with pytest.raises(DashboardDataError, match="missing columns"):
        load_crm_policy_comparison(tmp_path)


def test_streamlit_app_content_integrity_and_caveats() -> None:
    """Verifies that streamlit_app.py enforces analytical caveats, model designations,

    and non-causal language.
    """
    app_file = Path("streamlit_app.py")
    assert app_file.exists(), "streamlit_app.py must exist"
    code = app_file.read_text(encoding="utf-8").lower()

    # Model designations
    assert "rfm baseline" in code
    assert "recommended default" in code or "operational default" in code
    assert "expanded model" in code
    assert "challenger" in code

    # Retrospective temporal cohort caveat
    assert "retrospective temporal" in code
    assert "untouched" not in code
    assert "confirmatory test" not in code

    # Probability underprediction disclosure
    assert "underprediction" in code

    # Historical scope and non-causal language
    assert "2011" in code
    assert "revenue saved" not in code
    assert "protects £" not in code
    assert "universally optimal" not in code
    assert "one-time shoppers" not in code
