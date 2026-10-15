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
    _generate_markdown_report,
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
    """Verifies CRM outreach queue policy simulation, model/split identifiers,

    deterministic tie breaking, and exact analytical random-baseline calculation using k / n.
    """
    records = [
        {"customer_id": 1, "target_repeat_purchase_90d": 0, "net_commercial_spend": 1000.0},
        {"customer_id": 2, "target_repeat_purchase_90d": 0, "net_commercial_spend": 500.0},
        {"customer_id": 3, "target_repeat_purchase_90d": 1, "net_commercial_spend": 2000.0},
        {"customer_id": 4, "target_repeat_purchase_90d": 0, "net_commercial_spend": 50.0},
        {"customer_id": 5, "target_repeat_purchase_90d": 1, "net_commercial_spend": 100.0},
        {"customer_id": 6, "target_repeat_purchase_90d": 0, "net_commercial_spend": 200.0},
        {"customer_id": 7, "target_repeat_purchase_90d": 0, "net_commercial_spend": 300.0},
    ]
    df = pd.DataFrame(records)
    n = len(df)  # 7 customers
    total_spend = df["net_commercial_spend"].sum()  # 4150.0
    total_non_rep = (df["target_repeat_purchase_90d"] == 0).sum()  # 5 non-repeaters

    # Predicted probabilities
    probs = np.array([0.1, 0.4, 0.8, 0.1, 0.9, 0.3, 0.2])

    # Evaluate at 10% requested capacity -> k = max(1, round(0.10 * 7)) = 1
    # Actual fraction = 1 / 7 = 0.142857 != 0.10
    policies_df = evaluate_crm_queue_policies(
        eval_df=df,
        predicted_repeat_prob=probs,
        model_name="Test Model",
        evaluation_split="Test Split",
        capacities=(0.10,),
    )
    assert len(policies_df) == 4
    assert "model_name" in policies_df.columns
    assert "evaluation_split" in policies_df.columns
    assert (policies_df["model_name"] == "Test Model").all()
    assert (policies_df["evaluation_split"] == "Test Split").all()

    # Check Risk-first policy: customers 1 & 4 tie at risk 0.9. Deterministic tie-breaking selects customer 1 (asc ID).
    rf = policies_df[policies_df["policy"] == "Risk-first"].iloc[0]
    assert rf["selected_count"] == 1
    assert rf["selected_non_repeaters"] == 1
    assert rf["selected_non_repeat_rate"] == 1.0
    assert rf["historical_commercial_value_gbp"] == 1000.0

    # Check Random baseline analytical expectation uses actual fraction k / n = 1 / 7, NOT 0.10!
    rnd = policies_df[policies_df["policy"] == "Random baseline (analytical)"].iloc[0]
    expected_non_rep = round((1 / 7) * total_non_rep, 1)  # 5 / 7 = 0.714 -> 0.7
    expected_spend = round((1 / 7) * total_spend, 2)  # 4150 / 7 = 592.86
    # If it had used cap (0.10), spend would be 415.0. It MUST be 592.86!
    assert rnd["selected_count"] == 1
    assert np.isclose(rnd["selected_non_repeaters"], expected_non_rep)
    assert np.isclose(rnd["historical_commercial_value_gbp"], expected_spend)
    assert not np.isclose(rnd["historical_commercial_value_gbp"], 0.10 * total_spend)


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
    """Verifies that run_repeat_purchase_modeling executes end-to-end, covers both models

    across both cohorts, and outputs valid artifacts.
    """
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
        assert set(metrics_df["split_name"]) == {"Validation", "Retrospective Temporal Evaluation"}
        assert set(metrics_df["model_name"]) == {"RFM Baseline", "Expanded Model"}

        # Assert policy comparison covers both models and both evaluation splits (64 rows total)
        policy_df = pd.read_csv(policy_csv)
        assert len(policy_df) == 64
        assert "evaluation_split" in policy_df.columns
        assert "model_name" in policy_df.columns
        assert set(policy_df["evaluation_split"]) == {"Validation", "Retrospective Temporal Evaluation"}
        assert set(policy_df["model_name"]) == {"RFM Baseline", "Expanded Model"}
        assert set(policy_df["outreach_capacity"]) == {"1%", "5%", "10%", "20%"}

        # Check config json
        with open(config_json, encoding="utf-8") as fp:
            cfg = json.load(fp)
            assert cfg["recommended_default_model"] == "RFM Baseline"
            assert cfg["challenger_model"] == "Expanded Model"
            assert "selection_rationale" in cfg
            assert len(cfg["feature_sets"]["expanded_features"]) == 16


def test_evaluation_report_content_integrity(tmp_path: Path) -> None:
    """Verifies that the generated report avoids unsupported causal claims, claims of an untouched holdout,
    softens absolute lookahead/leakage claims, makes Expanded-Model calibration scope explicit,
    and avoids unproven 'one-time shoppers' assertions.

    Inspects the report generated during the test run in a temporary directory, as well as the
    repository-level report if present.
    """
    proc_dir = Path("data/processed")
    if (proc_dir / "rfm_snapshot_20101209.parquet").exists():
        # Generate fresh report via modeling pipeline in tmp_path
        run_repeat_purchase_modeling(
            processed_dir=proc_dir,
            reports_dir=tmp_path,
            random_state=42,
        )
        test_reports = [tmp_path / "repeat_purchase_model_evaluation.md"]
    else:
        # Fallback to direct report generator with mock dataframes
        mock_metrics = pd.DataFrame({
            "split_name": ["Validation", "Validation", "Retrospective Temporal Evaluation", "Retrospective Temporal Evaluation"],
            "model_name": ["RFM Baseline", "Expanded Model", "RFM Baseline", "Expanded Model"],
            "roc_auc": [0.8026, 0.8079, 0.7815, 0.7869],
            "average_precision": [0.6928, 0.6993, 0.7478, 0.7545],
            "brier_score": [0.1594, 0.1583, 0.2055, 0.2036],
            "top_decile_purchase_precision": [0.7717, 0.7919, 0.8973, 0.8973],
            "bottom_decile_non_purchase_rate": [0.9394, 0.9414, 0.9106, 0.9068],
        })
        mock_calib = pd.DataFrame({
            "decile": ["(0.004, 0.08]"] * 10,
            "count": [526] * 10,
            "mean_predicted_prob": [0.044] * 10,
            "observed_repeat_rate": [0.093] * 10,
            "abs_calibration_error": [0.049] * 10,
        })
        mock_coef = pd.DataFrame({"feature": ["recency_days"], "standardized_beta": [-1.2], "odds_ratio": [0.3]})
        mock_policy = pd.DataFrame({
            "evaluation_split": ["Validation"] * 4,
            "model_name": ["RFM Baseline"] * 4,
            "outreach_capacity": ["10%"] * 4,
            "target_customers": [495] * 4,
            "non_repeaters_captured": [470] * 4,
            "non_repeat_precision": [0.9495] * 4,
            "capture_share": [0.1396] * 4,
            "historical_commercial_spend": [18639.46] * 4,
            "spend_share": [0.0016] * 4,
            "expected_random_spend": [1146532.74] * 4,
            "random_spend_lift": [0.02] * 4,
            "policy": ["Risk-First", "Value-Aware", "Hybrid", "Random Baseline"],
        })
        tmp_report = tmp_path / "repeat_purchase_model_evaluation.md"
        _generate_markdown_report(
            report_path=tmp_report,
            metrics_summary_df=mock_metrics,
            calib_df=mock_calib,
            coef_exp_df=mock_coef,
            coef_rfm_df=mock_coef,
            policy_comparison_df=mock_policy,
            validation_cutoff="2011-06-10",
            temporal_cutoff="2011-09-09",
            config_data={"recommended_default_model": "RFM Baseline", "challenger_model": "Expanded Model"},
        )
        test_reports = [tmp_report]

    root_report = Path("reports/repeat_purchase_model_evaluation.md")
    if root_report.exists():
        test_reports.append(root_report)

    for report_file in test_reports:
        content = report_file.read_text(encoding="utf-8").lower()

        # 1. Softened lookahead and leakage wording assertions
        assert "guarantees zero look-ahead bias" not in content
        assert "guarantee zero look-ahead bias" not in content
        assert "eliminates all future information leakage" not in content
        assert "eliminate all future information leakage" not in content
        assert "mitigate look-ahead bias" in content
        assert "point-in-time" in content
        assert "leakage guards" in content

        # 2. Expanded Model calibration scope assertions
        assert "expanded model decile calibration" in content
        assert "decile calibration has not been evaluated or reported for the rfm baseline" in content
        assert "systematic probability underprediction" in content
        assert "coincides with that underprediction" in content
        assert "cause of this cohort base-rate shift remains unknown" in content
        assert "calibration was not evaluated across deciles for the rfm baseline" in content

        # 3. Risk-first queue assertions (avoid unverified "one-time shoppers" claim)
        assert "one-time shoppers" not in content
        assert "one-time buyers" not in content
        assert "<1% of cohort" in content

        # 4. Standard evaluation integrity assertions
        assert "untouched" not in content
        assert "confirmatory test" not in content
        assert "evaluated strictly once" not in content
        assert "frozen before any inspection" not in content
        assert "due to q4" not in content
        assert "holiday seasonal demand acceleration" not in content
        assert "autumn/holiday seasonal" not in content
        assert "safeguards revenue" not in content
        assert "revenue saved" not in content
        assert "protects £" not in content
        assert "universally optimal" not in content
        assert "optimal balance" not in content

        # 5. Required disclosures
        assert "retrospective temporal" in content
        assert "underprediction" in content
        assert "historical commercial spend" in content
