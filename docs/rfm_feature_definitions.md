# RFM Features and Customer Segments

RetenSight uses RFM—Recency, Frequency and Monetary value—to describe a customer's past purchasing behaviour. It also uses these features in a logistic-regression model that estimates the chance of a repeat purchase in the next 90 days.

## What the features mean

| Feature | Definition |
|---|---|
| **Recency (R)** | Whole days since the customer's latest qualifying merchandise purchase. A smaller number means a more recent purchase. |
| **Frequency (F)** | Number of distinct qualifying purchase invoices up to the scoring date. Invoice lines are not counted as separate orders. |
| **Monetary (M)** | Customer commercial net spend up to the scoring date. It includes merchandise sales, returns, shipping, discounts and manual commercial adjustments. Administrative settlements and bad debt are kept separate. |

A qualifying purchase is a customer-attributed, non-cancellation invoice with positive merchandise sales and positive net quantity. A shipping-only or manual-fee-only invoice does not count as a merchandise purchase. Two distinct invoices on the same day count as two orders; `distinct_purchase_days` records the number of purchase dates separately.

## RFM scoring

- **Recency:** customers are ranked by recency and assigned scores from 1 to 5. More recent customers receive higher scores.
- **Frequency:** scores follow fixed order-count ranges so ties at one purchase do not collapse quantile bins: 1 order = 1; 2 orders = 2; 3–4 = 3; 5–8 = 4; 9 or more = 5.
- **Monetary:** positive commercial spend is ranked into five groups. Customers with zero or negative commercial spend receive M = 0.

The three scores feed a documented decision table that maps all 125 positive `(R, F, M)` combinations, plus the non-positive-spend case, to 11 segments. The [CSV](../reports/crm_segment_decision_table.csv) and [JSON](../reports/crm_segment_decision_table.json) files are the source of truth for every mapping.

## Segment names

The project uses these segments: Champions, Loyal Customers, Potential Loyalists, New Customers, Promising, Can't Lose Them, At Risk, About To Sleep, Hibernating, Lost, and Negative or Zero Spend.

They describe historical behaviour, not a guarantee about what a customer will do next. Suggested CRM actions are hypotheses for planning; this project does not test campaign impact.

## Repeat-purchase model

The target is 1 if a customer makes at least one qualifying merchandise purchase during the 90 days after the scoring date, and 0 otherwise. Features are calculated only from transactions available by the scoring date.

Two logistic-regression models are compared:

- **RFM Baseline:** recency, frequency and net commercial spend.
- **Expanded Model:** the RFM features plus 13 additional historical features.

The June 10, 2011 cohort is used to govern the main recommendation. Its 4,952 customers have a 32.03% observed 90-day repeat rate. The September 9, 2011 cohort was inspected during development, so its results are reported as retrospective rather than as an untouched holdout.

The expanded model has slightly better headline metrics, but queue-level gains are small. RetenSight therefore recommends the simpler RFM model as the operational default.

## Important limitation

The December 9, 2011 snapshot contains 5,853 customers, but its future 90-day outcomes are not available in the source data. The target is stored as missing for this snapshot, not as zero.

The model ranks historical repeat-purchase likelihood. Without campaign exposure data, it cannot show that contacting a customer will prevent churn or increase sales.

See the [model evaluation report](../reports/repeat_purchase_model_evaluation.md) for metrics and the [RFM summary](../reports/rfm_segmentation_summary.md) for segment counts.
