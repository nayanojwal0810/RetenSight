"""Automated unit and integration tests for leakage-safe repeat-purchase modeling."""

import json
from pathlib import Path
import tempfile
from typing import Dict

import numpy as np
import pandas as pd
import pytest

from retensight.modeling import (
    EXPANDED_FEATURES,
    PROHIBITED_FEATURE_COLUMNS,
    RFM_BASELINE_FEATURES,
    SignedLogTransformer,
    build_modeling_pipeline,
    compute_calibration_table,
    compute_decile_metrics,
    evaluate_crm_queue_policies,
    evaluate_predictions,
    extract_coefficients,
    run_repeat_purchase_modeling,
    validate_chronological_boundaries,
    validate_feature_leakage,
)


def test_signed_log_transformer_mathematical_properties() -> None:
    """Verifies that SignedLogTransformer correctly transforms values:

    f(0) == 0, f(x > 0) == log1p(x), f(x < 0) == -log1p(|x|).
    """
    transformer = SignedLogTransformer()
    x = np.array([0.0, np.e - 1.0, -(np.e - 1.0), 10.0, -10.0])
    transformed = transformer.transform(x)

    assert np.isclose(transformed[0], 0.0)
    assert np.isclose(transformed[1], 1.0)
    assert np.isclose(transformed[2], -1.0)
    assert np.isclose(transformed[3], np.log(11.0))
    assert np.isclose(transformed[4], -np.log(11.0))


def test_feature_leakage_exclusion_guards() -> None:
    """Verifies that prohibited target or leakage columns raise an actionable ValueError."""
    # Permitted feature sets pass cleanly
    validate_feature_leakage(RFM_BASELINE_FEATURES)
    validate_feature_leakage(EXPANDED_FEATURES)

    # Prohibited columns trigger errors
    for col in PROHIBITED_FEATURE_COLUMNS:
        with pytest.raises(ValueError, match="Feature leakage detected"):
            validate_feature_leakage(list(RFM_BASELINE_FEATURES) + [col])

    # Dynamic target-prefixed columns trigger errors
    with pytest.raises(ValueError, match="Feature leakage detected"):
        validate_feature_leakage(list(RFM_BASELINE_FEATURES) + ["target_future_sales"])


def test_deterministic_preprocessing_and_reproducible_predictions() -> None:
    """Verifies that pipeline produces bitwise identical predictions across runs."""
    np.random.seed(42)
    n = 200
    p = 5
    X = np.random.randn(n, p) * 10.0
    y = np.random.binomial(1, 0.3, size=n)

    pipe1 = build_modeling_pipeline(random_state=42)
    pipe2 = build_modeling_pipeline(random_state=42)

    pipe1.fit(X, y)
    pipe2.fit(X, y)

    prob1 = pipe1.predict_proba(X)
    prob2 = pipe2.predict_proba(X)

    np.testing.assert_allclose(prob1, prob2, atol=1e-12)
    np.testing.assert_allclose(
        pipe1.named_steps["classifier"].coef_,
        pipe2.named_steps["classifier"].coef_,
        atol=1e-12,
    )


def test_decile_metrics_and_calibration_output() -> None:
    """Verifies calculation of top-decile precision, bottom-decile non-purchase rate, and calibration."""
    n = 100
    y_true = np.array([1] * 30 + [0] * 70)
    # Perfect probability assignment
    y_prob = np.array([0.95] * 30 + [0.05] * 70)
    customer_ids = np.arange(1001, 1001 + n)

    deciles = compute_decile_metrics(y_true, y_prob, customer_ids, fraction=0.10)
    assert deciles.decile_count == 10
    # Top 10 probabilities are 0.95 with true label 1
    assert deciles.top_decile_precision == 1.0
    # Bottom 10 probabilities are 0.05 with true label 0 (non-purchase = 1 - 0 = 1)
    assert deciles.bottom_decile_non_purchase_rate == 1.0

    # Calibration table
    calib = compute_calibration_table(y_true, y_prob, n_bins=5)
    assert len(calib) > 0
    assert "mean_predicted_prob" in calib.columns
    assert "observed_repeat_rate" in calib.columns
    assert "abs_calibration_error" in calib.columns


def test_crm_queue_policies_and_tie_handling() -> None:
    """Verifies CRM outreach queue policy simulation and deterministic tie breaking."""
    records = [
        {"customer_id": 1, "target_repeat_purchase_90d": 0, "net_commercial_spend": 1000.0},
        {"customer_id": 2, "target_repeat_purchase_90d": 0, "net_commercial_spend": 500.0},
        {"customer_id": 3, "target_repeat_purchase_90d": 1, "net_commercial_spend": 2000.0},
        {"customer_id": 4, "target_repeat_purchase_90d": 0, "net_commercial_spend": 50.0},
        {"customer_id": 5, "target_repeat_purchase_90d": 1, "net_commercial_spend": 100.0},
    ]
    df = pd.DataFrame(records)
    # Predicted probabilities: Customer 1 & 4 high risk (low prob); Customer 3 & 5 low risk (high prob)
    probs = np.array([0.1, 0.4, 0.8, 0.1, 0.9])

    # Evaluate at 40% capacity (k = 2 customers out of 5)
    policies_df = evaluate_crm_queue_policies(df, probs, capacities=(0.40,))
    assert len(policies_df) == 4  # 3 policies + random baseline

    # Check Risk-first policy: customers 1 & 4 have prob 0.1 (risk 0.9). Ties broken by customer_id asc (1 then 4).
    rf = policies_df[policies_df["policy"] == "Risk-first"].iloc[0]
    assert rf["selected_count"] == 2
    # Both customers 1 & 4 are non-repeaters (target == 0)
    assert rf["selected_non_repeaters"] == 2
    assert rf["selected_non_repeat_rate"] == 1.0
    assert rf["historical_commercial_value_gbp"] == 1050.0  # 1000 + 50

    # Check Value-aware policy: Expected Value at Risk = (1 - p) * spend
    # Cust 1: 0.9 * 1000 = 900
    # Cust 2: 0.6 * 500 = 300
    # Cust 3: 0.2 * 2000 = 400
    # Cust 4: 0.9 * 50 = 45
    # Cust 5: 0.1 * 100 = 10
    # Top 2 are Cust 1 (900) and Cust 3 (400)
    va = policies_df[policies_df["policy"] == "Value-aware"].iloc[0]
    assert va["selected_count"] == 2
    # Cust 1 is non-repeater, Cust 3 is repeater -> 1 non-repeater
    assert va["selected_non_repeaters"] == 1
    assert va["selected_non_repeat_rate"] == 0.5
    assert va["historical_commercial_value_gbp"] == 3000.0  # 1000 + 2000

    # Check Random baseline analytical expectation
    rnd = policies_df[policies_df["policy"] == "Random baseline (analytical)"].iloc[0]
    # Total non-repeaters = 3 out of 5 (60%). At 40% capacity (k=2): 2 * 0.6 = 1.2
    assert np.isclose(rnd["selected_non_repeaters"], 1.2)
    assert np.isclose(rnd["historical_commercial_value_gbp"], 0.40 * 3650.0)


def test_chronological_split_boundaries_and_benchmarks() -> None:
    """Verifies that actual processed snapshots satisfy all chronological split invariants

    and match independently verified benchmark counts.
    """
    proc_dir = Path("data/processed")
    if not (proc_dir / "rfm_snapshot_20101209.parquet").exists():
        pytest.skip("Processed snapshot files not present on disk.")

    snapshots = {
        "2010-12-09": pd.read_parquet(proc_dir / "rfm_snapshot_20101209.parquet"),
        "2011-06-10": pd.read_parquet(proc_dir / "rfm_snapshot_20110610.parquet"),
        "2011-09-09": pd.read_parquet(proc_dir / "rfm_snapshot_20110909.parquet"),
        "2011-12-09": pd.read_parquet(proc_dir / "rfm_snapshot_20111209.parquet"),
    }

    # Invariant: validate_chronological_boundaries passes without error
    validate_chronological_boundaries(snapshots)

    # Invariant: Evaluation cohorts have observed labels and exact counts
    s1 = snapshots["2010-12-09"]
    assert len(s1) == 4286
    assert s1["target_repeat_purchase_90d"].sum() == 1317

    s2 = snapshots["2011-06-10"]
    assert len(s2) == 4952
    assert s2["target_repeat_purchase_90d"].sum() == 1586

    s3 = snapshots["2011-09-09"]
    assert len(s3) == 5257
    assert s3["target_repeat_purchase_90d"].sum() == 2287

    # Invariant: Final snapshot 2011-12-09 has unobserved target labels
    s4 = snapshots["2011-12-09"]
    assert len(s4) == 5853
    assert (~s4["is_target_window_observed"]).all()
    assert s4["target_repeat_purchase_90d"].isna().all()


def test_full_modeling_pipeline_outputs_and_invariants() -> None:
    """Verifies that run_repeat_purchase_modeling executes end-to-end and outputs valid artifacts."""
    proc_dir = Path("data/processed")
    if not (proc_dir / "rfm_snapshot_20101209.parquet").exists():
        pytest.skip("Processed snapshot files not present on disk.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_reports = Path(tmp_dir)
        results = run_repeat_purchase_modeling(
            processed_dir=proc_dir,
            reports_dir=tmp_reports,
            random_state=42,
        )

        metrics_csv = tmp_reports / "repeat_purchase_model_metrics.csv"
        policy_csv = tmp_reports / "crm_queue_policy_comparison.csv"
        config_json = tmp_reports / "repeat_purchase_model_config.json"
        eval_md = tmp_reports / "repeat_purchase_model_evaluation.md"

        assert metrics_csv.exists() and metrics_csv.stat().st_size > 0
        assert policy_csv.exists() and policy_csv.stat().st_size > 0
        assert config_json.exists() and config_json.stat().st_size > 0
        assert eval_md.exists() and eval_md.stat().st_size > 0

        # Assert metrics table contents
        metrics_df = pd.read_csv(metrics_csv)
        assert len(metrics_df) == 4
        # Both models in validation achieve ROC-AUC >= 0.80
        val_expanded = metrics_df[
            (metrics_df["model_name"] == "Expanded Model")
            & (metrics_df["split_name"] == "Validation")
        ].iloc[0]
        assert val_expanded["roc_auc"] >= 0.80
        assert val_expanded["top_decile_precision"] >= 0.80

        # Holdout top decile precision >= 0.85 (over double the 43.50% base rate)
        ho_expanded = metrics_df[
            (metrics_df["model_name"] == "Expanded Model")
            & (metrics_df["split_name"] == "Temporal Holdout")
        ].iloc[0]
        assert ho_expanded["top_decile_precision"] >= 0.85
        assert ho_expanded["bottom_decile_non_purchase_rate"] >= 0.85

        # Check config json
        with open(config_json, encoding="utf-8") as fp:
            cfg = json.load(fp)
            assert cfg["selected_model_by_validation"] == "Expanded Model"
            assert len(cfg["feature_sets"]["expanded_features"]) == 16
