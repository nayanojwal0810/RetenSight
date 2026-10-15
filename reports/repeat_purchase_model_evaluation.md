# RetenSight — Repeat-Purchase Propensity Modeling and CRM Queue Evaluation Report

## Executive Summary

This report documents the design, implementation, and empirical evaluation of two point-in-time, explainable logistic regression models developed to estimate whether an active e-commerce customer will make at least one qualifying merchandise purchase in the forward 90 days following a scoring cutoff date.

- **RFM Baseline Model:** Formulated strictly from Recency ($R$), Frequency ($F$), and net commercial spend ($M$).
- **Expanded Model:** Extends the baseline with 13 additional point-in-time purchasing cadence, basket size, order value, cancellation behavior, and financial component features (16 total features).
- **Validation-Governed Model Recommendation:** Model selection is governed exclusively by the `2011-06-10` validation cohort. While the Expanded model achieves slight statistical improvements in validation ROC-AUC (0.8079 vs 0.8026) and Brier score (0.1583 vs 0.1594), CRM queue simulations across capacities demonstrate negligible practical targeting gain (e.g., capturing only 3 additional non-repeaters under Risk-first at 10% capacity, and 7 under Hybrid, while capturing £768.8k less historical spend under Value-aware). In accordance with parsimony and decision utility principles, the **simpler 3-feature RFM Baseline is recommended as the operational default**, retaining the Expanded model as an analytical challenger.
- **Retrospective Temporal Evaluation (`2011-09-09`):** The later chronological evaluation cohort was inspected during exploratory development and is presented transparently as a retrospective temporal evaluation rather than a prospective holdout. Both models demonstrate robust ranking separation in this cohort, achieving an 89.73% repeat rate in the top decile (compared to a 43.50% cohort base rate) and a 90.68%–91.06% non-purchase rate in the bottom decile.
- **CRM Outreach Prioritization Trade-offs:** Evaluated Risk-first, Value-aware, and Hybrid outreach policies across fixed capacity budgets (1%, 5%, 10%, 20%). Risk-first achieves the highest non-repeat capture precision (~95% in validation, ~91% in retrospective evaluation) but captures negligible historical commercial spend (<1%). Value-aware targets major historical commercial accounts (representing 35%–41% of cohort commercial spend at 10% capacity) with lower non-repeat precision. The Hybrid policy achieves an intermediate balance (81%–82% non-repeat precision in validation, representing ~7.4% of cohort historical spend). No single policy is universally superior across all business goals; the appropriate policy depends on commercial intervention costs and account value.

## 1. Strictly Chronological Walk-Forward Evaluation Design

To mitigate look-ahead bias and guard against future information leakage, the evaluation follows a strictly chronological walk-forward architecture. The methodology relies on defined chronological cutoffs, point-in-time feature construction, and explicit automated leakage guards, while acknowledging that no automated protocol can categorically prove the absence of every possible unobserved leakage source:

| Phase | Training Period / Cutoff | Forward Target Window | Evaluation Snapshot Cutoff | Cohort Size ($N$) | Observed Repeaters ($y=1$) | Base Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Validation Stage** | `2010-12-09 23:59:59` | `2010-12-10` to `2011-03-09` | `2011-06-10 23:59:59` | 4,952 | 1,586 | 32.03% |
| **Retrospective Temporal Stage** | `2010-12-09` + `2011-06-10` (9,238 rows) | `2011-06-11` to `2011-09-08` | `2011-09-09 23:59:59` | 5,257 | 2,287 | 43.50% |
| **Unobserved Production** | — | Unobserved (`2011-12-10` to `2012-03-08`) | `2011-12-09 12:50:00` | 5,853 | *None (<NA>)* | *Unobserved* |

### Chronological Separation and Methodological Integrity

- **Validation Boundary:** Cutoff 1 target window closes on `2011-03-09 23:59:59`, exactly 93 days prior to the Cutoff 2 evaluation scoring date (`2011-06-10 23:59:59`). No overlap exists.
- **Retrospective Evaluation Boundary:** Cutoff 2 target window closes on `2011-09-08 23:59:59`, exactly 1 day prior to the Cutoff 3 scoring date (`2011-09-09 23:59:59`). No overlap exists.
- **Cohort Base-Rate Shift:** The observed 90-day repeat rate shifts from 32.03% in the `2011-06-10` cohort to 43.50% in the `2011-09-09` cohort. The causal explanation for this shift is unknown from this observational analysis.
- **Repeated Observations:** Customers active across multiple cutoffs appear as distinct point-in-time scoring observations. Customer ID is never used as a predictive feature.
- **Evaluation Freeze:** Model recommendations and policy choices were derived solely from the validation stage. The retrospective temporal cohort was not used to select features, tune hyperparameters, or adjust decision thresholds.

## 2. Feature Engineering and Leakage Exclusion

### Feature Sets

1. **RFM Baseline (3 features):** `recency_days`, `frequency`, `net_commercial_spend`.
2. **Expanded Feature Set (16 features):** Baseline features plus `customer_tenure_days`, `distinct_purchase_days`, `total_items_purchased`, `merchandise_aov`, `commercial_order_value`, `net_spend_per_order`, `total_invoices_all`, `cancellation_invoice_count`, `monetary_merchandise_sales`, `monetary_merchandise_returns`, `monetary_shipping`, `monetary_discounts`, `monetary_manual_charges`.

### Preprocessing Pipeline

- **Deterministic Signed-Log Transformation:** Applied to all monetary and count features: $f(x) = \operatorname{sign}(x) \cdot \ln(1 + |x|)$. Smoothly manages heavy right-skewed purchasing totals as well as negative merchandise return amounts while mapping 0 identically to 0.
- **Median Imputation & Feature Standardization:** `SimpleImputer(strategy='median')` and `StandardScaler()` are fitted strictly on training data and applied downstream to prevent distribution leakage.

### Prohibited Columns (Enforced by Automated Leakage Guards)

The following columns are strictly excluded from all training and feature matrices: `customer_id`, `target_repeat_purchase_90d`, `target_spend_90d`, `target_ledger_balance_90d`, `is_target_window_observed`, `segment`, `r_score`, `f_score`, `m_score`, `rfm_score`, `snapshot_date`, `first_purchase_date`, `last_purchase_date`, `country`.

## 3. Model Evaluation Results

### Performance Metrics Comparison Table

| model_name     | split_name                        | snapshot_date | sample_count | positive_count | negative_count | base_rate | roc_auc | average_precision | brier_score | log_loss | top_decile_precision | bottom_decile_non_purchase_rate | decile_count |
| -------------- | --------------------------------- | ------------- | ------------ | -------------- | -------------- | --------- | ------- | ----------------- | ----------- | -------- | -------------------- | ------------------------------- | ------------ |
| RFM Baseline   | Validation                        | 2011-06-10    | 4952         | 1586           | 3366           | 0.3203    | 0.8026  | 0.6928            | 0.1594      | 0.4877   | 0.8566               | 0.9495                          | 495          |
| Expanded Model | Validation                        | 2011-06-10    | 4952         | 1586           | 3366           | 0.3203    | 0.8079  | 0.6993            | 0.1583      | 0.483    | 0.8545               | 0.9556                          | 495          |
| RFM Baseline   | Retrospective Temporal Evaluation | 2011-09-09    | 5257         | 2287           | 2970           | 0.435     | 0.7815  | 0.7478            | 0.2055      | 0.6068   | 0.8973               | 0.9106                          | 526          |
| Expanded Model | Retrospective Temporal Evaluation | 2011-09-09    | 5257         | 2287           | 2970           | 0.435     | 0.7869  | 0.7545            | 0.2036      | 0.6048   | 0.8973               | 0.9068                          | 526          |

### Key Analytical Insights

1. **Validation Metrics Comparison:** On the `2011-06-10` validation set, the Expanded Model achieves slightly higher ROC-AUC (0.8079 vs 0.8026) and average precision (0.6993 vs 0.6928), with a marginally lower Brier score (0.1583 vs 0.1594). However, the top-decile repeat rate is virtually identical (85.45% Expanded vs 85.66% Baseline).
2. **Retrospective Temporal Performance:** On the `2011-09-09` cohort, both models achieve identical top-decile repeat precision (89.73%), and the RFM Baseline exhibits a slightly higher bottom-decile non-purchase rate (91.06% vs 90.68%). ROC-AUC and average precision remain modestly higher for the Expanded model (0.7869 vs 0.7815, and 0.7545 vs 0.7478).
3. **Practical Utility Conclusion:** Across both evaluation cohorts, the predictive differences between the two models are minor. The additional complexity of maintaining 16 features does not produce a commensurate gain in practical customer ranking.

## 4. Calibration Evidence and Underprediction Analysis

### Expanded Model Decile Calibration on Retrospective Temporal Cohort (`2011-09-09`)

*Calibration Scope:* Decile calibration was evaluated specifically for the **Expanded Model** on the retrospective temporal evaluation cohort (`2011-09-09`). Decile calibration has not been evaluated or reported for the RFM Baseline model.

| decile                         | sample_count | mean_predicted_prob | observed_repeat_rate | abs_calibration_error |
| ------------------------------ | ------------ | ------------------- | -------------------- | --------------------- |
| (0.013999999999999999, 0.0547] | 526          | 0.044               | 0.0932               | 0.0492                |
| (0.0547, 0.0755]               | 526          | 0.0647              | 0.1806               | 0.1159                |
| (0.0755, 0.111]                | 525          | 0.0917              | 0.221                | 0.1293                |
| (0.111, 0.151]                 | 526          | 0.129               | 0.27                 | 0.141                 |
| (0.151, 0.214]                 | 526          | 0.1825              | 0.384                | 0.2015                |
| (0.214, 0.288]                 | 525          | 0.2495              | 0.4324               | 0.1829                |
| (0.288, 0.391]                 | 526          | 0.3377              | 0.5095               | 0.1718                |
| (0.391, 0.544]                 | 525          | 0.4616              | 0.6019               | 0.1403                |
| (0.544, 0.733]                 | 526          | 0.631               | 0.7605               | 0.1295                |
| (0.733, 0.999]                 | 526          | 0.8564              | 0.8973               | 0.0409                |

> [!IMPORTANT]
> **Calibration Finding:** Across all 10 reported deciles for the Expanded Model in the `2011-09-09` retrospective temporal cohort, the observed repeat rate exceeds the mean predicted probability. This demonstrates **systematic probability underprediction** for this model. An observed upward shift in cohort repeat base rate (from 32.03% in validation to 43.50% in this evaluation window) coincides with that underprediction, while the underlying cause of this cohort base-rate shift remains unknown from observational transaction data. While predicted probabilities maintain strict monotonic ordering across deciles (from 4.40% in Decile 1 to 85.64% in Decile 10), they are not well-calibrated in an absolute frequency sense. In accordance with evaluation integrity, no post-hoc calibrator was fitted to this cohort, and raw probability estimates from the Expanded Model must be interpreted with this underprediction in mind.

## 5. Model Explainability and Standardized Coefficients

The tables below report standardized logistic regression coefficients $\beta_j$ and odds ratios $\exp(\beta_j)$ per 1 standard deviation increase in the signed-log transformed feature.

### Expanded Model Coefficients

| feature                      | standardized_coefficient | odds_ratio_per_sd | direction            | transformation               |
| ---------------------------- | ------------------------ | ----------------- | -------------------- | ---------------------------- |
| distinct_purchase_days       | 1.2999                   | 3.669             | Increases Propensity | signed_log + standard_scaler |
| total_items_purchased        | 0.173                    | 1.1889            | Increases Propensity | signed_log + standard_scaler |
| monetary_merchandise_sales   | 0.1618                   | 1.1756            | Increases Propensity | signed_log + standard_scaler |
| net_commercial_spend         | 0.1397                   | 1.1499            | Increases Propensity | signed_log + standard_scaler |
| cancellation_invoice_count   | 0.1176                   | 1.1248            | Increases Propensity | signed_log + standard_scaler |
| monetary_shipping            | 0.1112                   | 1.1176            | Increases Propensity | signed_log + standard_scaler |
| commercial_order_value       | 0.095                    | 1.0996            | Increases Propensity | signed_log + standard_scaler |
| monetary_merchandise_returns | 0.0816                   | 1.085             | Increases Propensity | signed_log + standard_scaler |
| net_spend_per_order          | 0.0373                   | 1.038             | Increases Propensity | signed_log + standard_scaler |
| monetary_manual_charges      | 0.0259                   | 1.0263            | Increases Propensity | signed_log + standard_scaler |
| total_invoices_all           | 0.011                    | 1.0111            | Increases Propensity | signed_log + standard_scaler |
| monetary_discounts           | -0.0304                  | 0.9701            | Decreases Propensity | signed_log + standard_scaler |
| merchandise_aov              | -0.1758                  | 0.8388            | Decreases Propensity | signed_log + standard_scaler |
| recency_days                 | -0.2494                  | 0.7792            | Decreases Propensity | signed_log + standard_scaler |
| customer_tenure_days         | -0.2989                  | 0.7417            | Decreases Propensity | signed_log + standard_scaler |
| frequency                    | -0.4196                  | 0.6573            | Decreases Propensity | signed_log + standard_scaler |

### RFM Baseline Coefficients

| feature              | standardized_coefficient | odds_ratio_per_sd | direction            | transformation               |
| -------------------- | ------------------------ | ----------------- | -------------------- | ---------------------------- |
| frequency            | 0.693                    | 1.9998            | Increases Propensity | signed_log + standard_scaler |
| net_commercial_spend | 0.4121                   | 1.51              | Increases Propensity | signed_log + standard_scaler |
| recency_days         | -0.4501                  | 0.6375            | Decreases Propensity | signed_log + standard_scaler |

> [!IMPORTANT]
> **Observational Disclaimer:** These coefficients reflect conditional statistical associations in observational transaction data, **not causal mechanisms**. A positive coefficient indicates that customers with higher historical engagement were more likely to repeat under historical conditions. It does not imply that marketing actions designed to increase frequency or spend will causally alter repeat purchase propensity by that odds ratio.

## 6. CRM Outreach Queue Prioritization Policies

To evaluate decision utility under capacity constraints, four targeting policies were simulated across both evaluation cohorts at 1%, 5%, 10%, and 20% capacity budgets. Below is the primary comparison at **10% outreach capacity**:

| evaluation_split                  | model_name     | outreach_capacity | outreach_capacity_fraction | selected_count | policy                       | selected_non_repeaters | selected_non_repeat_rate | share_of_all_non_repeaters_captured | historical_commercial_value_gbp | share_of_cohort_commercial_value |
| --------------------------------- | -------------- | ----------------- | -------------------------- | -------------- | ---------------------------- | ---------------------- | ------------------------ | ----------------------------------- | ------------------------------- | -------------------------------- |
| Validation                        | RFM Baseline   | 10%               | 0.1                        | 495            | Risk-first                   | 470.0                  | 0.9495                   | 0.1396                              | 53442.99                        | 0.0047                           |
| Validation                        | RFM Baseline   | 10%               | 0.1                        | 495            | Value-aware                  | 236.0                  | 0.4768                   | 0.0701                              | 4736269.92                      | 0.4129                           |
| Validation                        | RFM Baseline   | 10%               | 0.1                        | 495            | Hybrid                       | 401.0                  | 0.8101                   | 0.1191                              | 854894.49                       | 0.0745                           |
| Validation                        | RFM Baseline   | 10%               | 0.1                        | 495            | Random baseline (analytical) | 336.5                  | 0.6798                   | 0.1                                 | 1146539.06                      | 0.1                              |
| Validation                        | Expanded Model | 10%               | 0.1                        | 495            | Risk-first                   | 473.0                  | 0.9556                   | 0.1405                              | 73706.57                        | 0.0064                           |
| Validation                        | Expanded Model | 10%               | 0.1                        | 495            | Value-aware                  | 253.0                  | 0.5111                   | 0.0752                              | 3967461.89                      | 0.3459                           |
| Validation                        | Expanded Model | 10%               | 0.1                        | 495            | Hybrid                       | 408.0                  | 0.8242                   | 0.1212                              | 844946.5                        | 0.0737                           |
| Validation                        | Expanded Model | 10%               | 0.1                        | 495            | Random baseline (analytical) | 336.5                  | 0.6798                   | 0.1                                 | 1146539.06                      | 0.1                              |
| Retrospective Temporal Evaluation | RFM Baseline   | 10%               | 0.1                        | 526            | Risk-first                   | 479.0                  | 0.9106                   | 0.1613                              | 60843.24                        | 0.0046                           |
| Retrospective Temporal Evaluation | RFM Baseline   | 10%               | 0.1                        | 526            | Value-aware                  | 181.0                  | 0.3441                   | 0.0609                              | 5944424.7                       | 0.4483                           |
| Retrospective Temporal Evaluation | RFM Baseline   | 10%               | 0.1                        | 526            | Hybrid                       | 391.0                  | 0.7433                   | 0.1316                              | 940834.32                       | 0.071                            |
| Retrospective Temporal Evaluation | RFM Baseline   | 10%               | 0.1                        | 526            | Random baseline (analytical) | 297.2                  | 0.565                    | 0.1001                              | 1326755.01                      | 0.1001                           |
| Retrospective Temporal Evaluation | Expanded Model | 10%               | 0.1                        | 526            | Risk-first                   | 477.0                  | 0.9068                   | 0.1606                              | 82584.55                        | 0.0062                           |
| Retrospective Temporal Evaluation | Expanded Model | 10%               | 0.1                        | 526            | Value-aware                  | 193.0                  | 0.3669                   | 0.065                               | 4848157.89                      | 0.3656                           |
| Retrospective Temporal Evaluation | Expanded Model | 10%               | 0.1                        | 526            | Hybrid                       | 399.0                  | 0.7586                   | 0.1343                              | 897205.33                       | 0.0677                           |
| Retrospective Temporal Evaluation | Expanded Model | 10%               | 0.1                        | 526            | Random baseline (analytical) | 297.2                  | 0.565                    | 0.1001                              | 1326755.01                      | 0.1001                           |

*Note: Full comparison tables across all capacities (1%, 5%, 10%, 20%) are available in `reports/crm_queue_policy_comparison.csv`.*

### CRM Policy Decision Outcomes and Trade-Offs

- **RFM Baseline vs. Expanded Model in Validation (10% Capacity):**
  - Under **Risk-First**, the Expanded model captures 473 non-repeaters (95.56% non-repeat rate) versus 470 for the RFM Baseline (94.95%), a gain of only 3 additional accounts out of 495 contacts.
  - Under **Hybrid**, the Expanded model captures 408 non-repeaters (82.42% non-repeat rate) versus 401 for the RFM Baseline (81.01%), a gain of only 7 accounts, with nearly identical historical spend represented (£844.9k vs £854.9k).
  - Under **Value-Aware**, the RFM Baseline captures substantially more historical commercial spend (£4.74M, 41.29% of cohort spend) than the Expanded model (£3.97M, 34.59% of cohort spend), while capturing 236 non-repeaters versus 253.
- **Trade-Off Summary across Policies:**
  - **Risk-First Policy:** Maximizes non-repeat capture precision (~95% in validation, ~91% in retrospective evaluation) by targeting customers with lowest predicted return likelihood. However, these selected accounts account for a minimal share of historical commercial spend (<1% of cohort spend across both evaluation cohorts).
  - **Value-Aware Policy:** Prioritizes accounts with the highest historical commercial spend at risk, representing 35%–41% of cohort commercial spend at 10% capacity. Because high spenders repeat more often than average, non-repeat precision is lower (37%–51%).
  - **Hybrid Policy:** Combines normalized risk rank and spend rank ($0.5 \times \text{Risk} + 0.5 \times \text{Spend}$), achieving 74%–82% non-repeat precision while representing 6.8%–7.5% of cohort historical spend.
  - **Policy Selection Depends on Operating Context:** No single policy serves all objectives. The appropriate CRM policy depends on operational constraints, intervention costs, and account value. Low-cost automated re-engagement favors Risk-First; high-touch account management favors Value-Aware; budget-constrained marketing campaigns favor Hybrid.

## 7. Operational Limitations and Deployment Safeguards

1. **No Causal Uplift or Preserved Revenue Claims:** Observed figures represent historical commercial spend associated with selected customers. They do not measure incremental retention, campaign uplift, causal impact, profit, or customer lifetime value. Observational data cannot establish how customers would respond to intervention.
2. **Retrospective Status of Later Evaluation Cohort:** The `2011-09-09` cohort was inspected during development and serves as a retrospective temporal benchmark. It must not be treated as a prospective holdout benchmark.
3. **Probability Underprediction & Calibration Scope:** Decile calibration was evaluated exclusively for the Expanded Model on the retrospective temporal evaluation cohort (`2011-09-09`), where its reported deciles exhibit systematic probability underprediction. An observed upward shift in cohort repeat base rate coincides with that underprediction, while the underlying cause of this cohort base-rate shift is unknown from observational data. Calibration was not evaluated across deciles for the RFM Baseline. While ranking discrimination remains effective for customer prioritization queues, raw probability estimates from the Expanded Model should not be interpreted as absolute calibrated frequencies.
4. **Unobserved Cutoff:** The `2011-12-09` snapshot represents production scoring as of dataset conclusion. Forward labels are strictly unobserved and were excluded from all training, validation, and evaluation.
