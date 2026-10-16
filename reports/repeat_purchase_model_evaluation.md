# Repeat-Purchase Modelling Results

RetenSight compares two logistic-regression models that estimate whether a customer will make at least one qualifying merchandise purchase in the next 90 days.

## Main finding

The recommended default is the **RFM Baseline**, which uses recency, frequency and net commercial spend. The Expanded Model uses 16 historical features and provides only small improvements in the observed validation metrics and practical queue results.

## Model performance

| Model | Cohort | Customers | Observed repeat rate | ROC-AUC | Average precision | Brier score | Log loss | Top-decile repeat rate | Bottom-decile non-repeat rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RFM Baseline | Validation | 4,952 | 32.03% | 0.8026 | 0.6928 | 0.1594 | 0.4877 | 85.66% | 94.95% |
| Expanded Model | Validation | 4,952 | 32.03% | 0.8079 | 0.6993 | 0.1583 | 0.4830 | 85.45% | 95.56% |
| RFM Baseline | Retrospective temporal evaluation | 5,257 | 43.50% | 0.7815 | 0.7478 | 0.2055 | 0.6068 | 89.73% | 91.06% |
| Expanded Model | Retrospective temporal evaluation | 5,257 | 43.50% | 0.7869 | 0.7545 | 0.2036 | 0.6048 | 89.73% | 90.68% |

The expanded model scores slightly better on several statistical metrics, but the gains are small. Its extra features do not show a convincing improvement in practical CRM queue selection.

## Contact strategies at 10% capacity

The table below uses the RFM model on the June 2011 validation cohort. Each strategy selects 495 customers.

| Strategy | Contacts | Non-repeat precision | Share of non-repeaters captured | Historical spend | Share of cohort spend |
|---|---:|---:|---:|---:|---:|
| Risk-first | 495 | 94.95% | 13.96% | £53,443 | 0.47% |
| Hybrid | 495 | 81.01% | 11.91% | £854,894 | 7.45% |
| Value-aware | 495 | 47.68% | 7.01% | £4,736,270 | 41.29% |
| Random benchmark | 495 | 67.98% | 10.00% | £1,146,539 | 10.00% |

- **Risk-first** prioritizes customers least likely to repeat. At 10% capacity it reaches about 95% non-repeat precision but represents less than 1% of cohort historical commercial spend.
- **Value-aware** selects customers with higher historical spend but has lower non-repeat precision.
- **Hybrid** balances risk and historical spend. Random selection provides a reference point.

## Method and limitations

Features are built point-in-time from data available by the scoring date. The pipeline uses leakage guards to mitigate look-ahead bias, although automated checks cannot prove the absence of every possible source of leakage.

The June 2011 cohort governs model selection. The September 2011 cohort was inspected during development and is a retrospective temporal evaluation, not a prospective holdout.

Expanded Model decile calibration was checked on the retrospective temporal cohort. Decile calibration has not been evaluated or reported for the RFM Baseline. The Expanded Model shows systematic probability underprediction; the higher observed repeat rate in the later cohort coincides with that underprediction, but the cause of this cohort base-rate shift remains unknown. Calibration was not evaluated across deciles for the RFM Baseline.

Historical commercial spend describes past transactions. It does not measure incremental campaign value, profit, customer lifetime value, or causal impact. The data contains no campaign exposure or treatment information.

The final December 2011 customer snapshot has no observed forward 90-day target. Those outcomes remain missing, not zero.

See [model metrics](repeat_purchase_model_metrics.csv) and [CRM queue policy results](crm_queue_policy_comparison.csv) for the machine-readable outputs.
