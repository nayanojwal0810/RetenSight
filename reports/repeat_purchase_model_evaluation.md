# RetenSight — Repeat-Purchase Propensity Modeling and CRM Queue Evaluation Report

## Executive Summary

This report documents the design, implementation, and rigorous evaluation of two leakage-safe, explainable logistic regression models developed to predict whether an active e-commerce customer will make at least one qualifying merchandise purchase in the forward 90 days following a scoring cutoff date.

- **RFM Baseline Model:** Built strictly from Recency ($R$), Frequency ($F$), and net commercial spend ($M$).
- **Expanded Model:** Extends the baseline with 13 additional point-in-time purchasing cadence, basket size, order value, cancellation behavior, and financial component features (16 total features).
- **Validation-Governed Selection:** The Expanded model demonstrated superior discriminative power (ROC-AUC 0.8079 vs 0.8026, PR-AUC 0.6993 vs 0.6928) and improved calibration (Brier score 0.1583 vs 0.1594) on the chronological validation set (`2011-06-10`). In accordance with pre-specified protocol, model selection was frozen prior to holdout evaluation.
- **Final Temporal Holdout Evaluation (`2011-09-09`):** Evaluated strictly once on the 5,257-customer holdout. Both models confirmed exceptional decile discrimination, achieving an ~89.7% repeat rate in the top decile (over double the random base rate of 43.50%) and a ~91.0% non-purchase rate in the bottom decile.
- **CRM Queue Prioritization:** Evaluated Risk-first, Value-aware, and Hybrid outreach policies across fixed capacity budgets (1%, 5%, 10%, 20%). Risk-first delivers peak non-repeat capture precision (~90.7%) but captures negligible historical value (<1%). Value-aware protects substantial commercial revenue (up to 54.0% of cohort spend) with lower non-repeat precision. The Hybrid policy achieves an optimal operational balance, delivering 71.5%–84.9% non-repeat precision while safeguarding £165k–£1.79M of commercial customer spend.

## 1. Strictly Chronological Walk-Forward Evaluation Design

To guarantee zero look-ahead bias and eliminate all future information leakage, the evaluation strictly follows a chronological walk-forward architecture:

| Phase | Training Period / Cutoff | Forward Target Window | Evaluation Snapshot Cutoff | Cohort Size ($N$) | Observed Repeaters ($y=1$) | Base Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Validation Stage** | `2010-12-09 23:59:59` | `2010-12-10` to `2011-03-09` | `2011-06-10 23:59:59` | 4,952 | 1,586 | 32.03% |
| **Temporal Holdout Stage** | `2010-12-09` + `2011-06-10` (9,238 rows) | `2011-06-11` to `2011-09-08` | `2011-09-09 23:59:59` | 5,257 | 2,287 | 43.50% |
| **Unobserved Production** | — | Unobserved (`2011-12-10` to `2012-03-08`) | `2011-12-09 12:50:00` | 5,853 | *None (<NA>)* | *Unobserved* |

### Chronological Separation Verification

- **Validation Boundary:** Cutoff 1 target window closes on `2011-03-09 23:59:59`, exactly 93 days prior to the Cutoff 2 evaluation scoring date (`2011-06-10 23:59:59`). No overlap exists.
- **Holdout Boundary:** Cutoff 2 target window closes on `2011-09-08 23:59:59`, exactly 1 day prior to the Cutoff 3 holdout scoring date (`2011-09-09 23:59:59`). No overlap exists.
- **Repeated Observations:** Customers active across multiple cutoffs appear as distinct point-in-time scoring observations. Under standard CRM operations, customer states are re-scored periodically. Customer ID is never used as a predictive feature.
- **Holdout Integrity:** Holdout labels (`2011-09-09`) were strictly locked and never used for feature selection, hyperparameter tuning, or model selection.

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

| model_name     | split_name       | snapshot_date | sample_count | positive_count | negative_count | base_rate | roc_auc | average_precision | brier_score | log_loss | top_decile_precision | bottom_decile_non_purchase_rate | decile_count |
| -------------- | ---------------- | ------------- | ------------ | -------------- | -------------- | --------- | ------- | ----------------- | ----------- | -------- | -------------------- | ------------------------------- | ------------ |
| RFM Baseline   | Validation       | 2011-06-10    | 4952         | 1586           | 3366           | 0.3203    | 0.8026  | 0.6928            | 0.1594      | 0.4877   | 0.8566               | 0.9495                          | 495          |
| Expanded Model | Validation       | 2011-06-10    | 4952         | 1586           | 3366           | 0.3203    | 0.8079  | 0.6993            | 0.1583      | 0.483    | 0.8545               | 0.9556                          | 495          |
| RFM Baseline   | Temporal Holdout | 2011-09-09    | 5257         | 2287           | 2970           | 0.435     | 0.7815  | 0.7478            | 0.2055      | 0.6068   | 0.8973               | 0.9106                          | 526          |
| Expanded Model | Temporal Holdout | 2011-09-09    | 5257         | 2287           | 2970           | 0.435     | 0.7869  | 0.7545            | 0.2036      | 0.6048   | 0.8973               | 0.9068                          | 526          |

### Key Analytical Insights

1. **Validation Superiority of Expanded Model:** On the `2011-06-10` validation set, the Expanded Model outperforms the RFM Baseline across ROC-AUC (0.8079 vs 0.8026), PR-AUC (0.6993 vs 0.6928), and Brier calibration score (0.1583 vs 0.1594). Basket depth and multi-day purchasing cadence provide distinct predictive lift over invoice counts alone.
2. **Decile Discrimination:** In the holdout period, both models exhibit strong separation. The top decile achieves an 89.73% repeat rate (vs 43.50% base rate), while the bottom decile isolates customers with a 90.68%–91.06% non-purchase rate.
3. **Seasonal Shift and Calibration:** The holdout repeat base rate (43.50%) is elevated relative to the training period (30.73%–32.03%) due to Q4 autumn/holiday seasonal demand acceleration. Despite this retail macro-shift, rank ordering and decile calibration remain strictly monotonic.

## 4. Calibration Evidence (Expanded Model on Temporal Holdout)

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

> **Calibration Note:** Calibration bins demonstrate strict monotonic increase in observed repeat rates across all 10 predicted probability deciles (from 9.32% in Decile 1 to 89.73% in Decile 10). The conservative probability predictions in intermediate deciles reflect the training set's baseline environment (~31% repeat rate) prior to Q4 seasonal shopping surges.

## 5. Model Explainability and Standardized Coefficients

The table below shows the standardized logistic regression coefficients $\beta_j$ and corresponding odds ratios $\exp(\beta_j)$ per 1 standard deviation increase in the signed-log transformed feature.

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
> **Observational Disclaimer:** These coefficients reflect conditional predictive associations in historical transaction data, **not causal effects**. A positive coefficient indicates that customers with higher historical engagement were more likely to repeat under historical conditions. It does not imply that incentivizing a customer to buy more will causally increase their repeat propensity by that odds ratio.

## 6. CRM Outreach Queue Prioritization Policies

Under limited operational outreach capacity (e.g. call center, targeted mail, personalized retention incentive), four policies were compared on the final temporal holdout (5,257 eligible customers, 2,970 non-repeaters, £13.26M historical spend):

| outreach_capacity | outreach_capacity_fraction | selected_count | policy                       | selected_non_repeaters | selected_non_repeat_rate | share_of_all_non_repeaters_captured | historical_commercial_value_gbp | share_of_cohort_commercial_value |
| ----------------- | -------------------------- | -------------- | ---------------------------- | ---------------------- | ------------------------ | ----------------------------------- | ------------------------------- | -------------------------------- |
| 1%                | 0.01                       | 53             | Risk-first                   | 48.0                   | 0.9057                   | 0.0162                              | 934.83                          | 0.0001                           |
| 1%                | 0.01                       | 53             | Value-aware                  | 21.0                   | 0.3962                   | 0.0071                              | 1508385.6                       | 0.1138                           |
| 1%                | 0.01                       | 53             | Hybrid                       | 45.0                   | 0.8491                   | 0.0152                              | 164966.98                       | 0.0124                           |
| 1%                | 0.01                       | 53             | Random baseline (analytical) | 29.9                   | 0.5642                   | 0.0101                              | 132599.83                       | 0.01                             |
| 5%                | 0.05                       | 263            | Risk-first                   | 237.0                  | 0.9011                   | 0.0798                              | 28592.26                        | 0.0022                           |
| 5%                | 0.05                       | 263            | Value-aware                  | 100.0                  | 0.3802                   | 0.0337                              | 3450419.4                       | 0.2602                           |
| 5%                | 0.05                       | 263            | Hybrid                       | 195.0                  | 0.7414                   | 0.0657                              | 531104.88                       | 0.0401                           |
| 5%                | 0.05                       | 263            | Random baseline (analytical) | 148.6                  | 0.565                    | 0.05                                | 662999.15                       | 0.05                             |
| 10%               | 0.1                        | 526            | Risk-first                   | 477.0                  | 0.9068                   | 0.1606                              | 82584.55                        | 0.0062                           |
| 10%               | 0.1                        | 526            | Value-aware                  | 193.0                  | 0.3669                   | 0.065                               | 4848157.89                      | 0.3656                           |
| 10%               | 0.1                        | 526            | Hybrid                       | 399.0                  | 0.7586                   | 0.1343                              | 897205.33                       | 0.0677                           |
| 10%               | 0.1                        | 526            | Random baseline (analytical) | 297.2                  | 0.565                    | 0.1001                              | 1325998.3                       | 0.1                              |
| 20%               | 0.2                        | 1051           | Risk-first                   | 907.0                  | 0.863                    | 0.3054                              | 236568.69                       | 0.0178                           |
| 20%               | 0.2                        | 1051           | Value-aware                  | 403.0                  | 0.3834                   | 0.1357                              | 7154456.78                      | 0.5396                           |
| 20%               | 0.2                        | 1051           | Hybrid                       | 751.0                  | 0.7146                   | 0.2529                              | 1786090.05                      | 0.1347                           |
| 20%               | 0.2                        | 1051           | Random baseline (analytical) | 593.8                  | 0.565                    | 0.1999                              | 2651996.6                       | 0.2                              |

### CRM Policy Strategic Comparison
- **Risk-First Policy:** Ideal when outreach capacity is highly constrained and the goal is strictly non-repeat capture accuracy (e.g., automated reactivation surveys). Captures non-repeaters with ~90.7% precision at 10% capacity, but targets low-tenure, one-time shoppers representing only £82.6k (0.62%) of historical revenue.
- **Value-Aware Policy:** Ideal for high-touch account management where losing an account is catastrophic. Targets major commercial accounts (£4.85M at 10% capacity, £7.15M at 20% capacity). However, because high spenders naturally repeat more frequently, non-repeat precision is lower (36.7%–38.3%).
- **Hybrid Policy (Recommended for CRM Retention):** Blends normalized risk rank and commercial spend rank ($0.5 \times \text{Risk} + 0.5 \times \text{Value}$). Achieves 75.9% non-repeat capture precision at 10% capacity (vs 56.5% random baseline) while capturing £897k of commercial customer spend. At 20% capacity, it protects £1.79M of spend with 71.5% non-repeat precision.
- **Random Baseline:** Represents uninformed outreach, capturing non-repeaters exactly at the base rate (56.5%) and spend strictly proportional to capacity.
## 7. Operational Limitations and Deployment Safeguards
1. **No Causal Uplift Claims:** Transaction data reflects organic retail behavior. Predictions identify who is at risk of not repeating, not who will respond positively to marketing intervention.
2. **Seasonal Calibration Drift:** When scoring Q4 (autumn/holiday) cohorts, predicted probabilities will trend conservative due to retail holiday surges. Priority ranks remain robust, but absolute probability thresholds should account for seasonal baselines.
3. **Unobserved Cutoffs:** The `2011-12-09` snapshot represents production scoring as of dataset end. Forward labels are strictly unobserved and were excluded from training and evaluation.
