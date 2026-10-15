# RetenSight — Customer RFM Analytics & Segmentation Summary

## Executive Summary

This report details the customer-level RFM features, deterministic scoring, explainable CRM segmentation, 
and forward 90-day repeat-purchase rates across chronological evaluation cutoffs for the UCI Online Retail II dataset.

## Cutoff Overview & Forward 90-Day Target Calibration

| Evaluation Cutoff | Eligible Customers | Mean Recency (Days) | Mean Frequency | Total Net Spend (£) | 90-Day Repeat Buyers | Repeat Purchase Rate (%) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2010-12-09` | 4,286 | 89.6 | 4.43 | £8,434,360.82 | 1,317 | 30.7% |
| `2011-06-10` | 4,952 | 170.3 | 5.27 | £11,472,463.65 | 1,586 | 32.0% |
| `2011-09-10` | 5,257 | 206.4 | 5.71 | £13,262,651.64 | 2,289 | 43.5% |
| `2011-12-09` | 5,853 | 199.2 | 6.25 | £16,427,051.43 | N/A | Unobserved (Dataset End) |

## Cross-Cutoff CRM Segment Distribution

| CRM Segment | `2010-12-09` Count (%) | `2011-06-10` Count (%) | `2011-09-10` Count (%) | `2011-12-09` Count (%) |
| :--- | ---: | ---: | ---: | ---: |
| **Champions** | 843 (19.7%) | 1,124 (22.7%) | 1,253 (23.8%) | 1,393 (23.8%) |
| **Loyal Customers** | 399 (9.3%) | 589 (11.9%) | 580 (11.0%) | 747 (12.8%) |
| **Potential Loyalists** | 619 (14.4%) | 587 (11.8%) | 612 (11.6%) | 709 (12.1%) |
| **New Customers** | 249 (5.8%) | 268 (5.4%) | 236 (4.5%) | 235 (4.0%) |
| **Promising** | 454 (10.6%) | 399 (8.1%) | 469 (8.9%) | 417 (7.1%) |
| **About To Sleep** | 509 (11.9%) | 664 (13.4%) | 649 (12.3%) | 676 (11.6%) |
| **At Risk** | 432 (10.1%) | 455 (9.2%) | 533 (10.1%) | 642 (11.0%) |
| **Can't Lose Them** | 23 (0.5%) | 29 (0.6%) | 44 (0.8%) | 65 (1.1%) |
| **Hibernating** | 157 (3.7%) | 200 (4.0%) | 210 (4.0%) | 234 (4.0%) |
| **Lost** | 581 (13.6%) | 616 (12.4%) | 649 (12.3%) | 709 (12.1%) |
| **Negative or Zero Spend** | 20 (0.5%) | 21 (0.4%) | 22 (0.4%) | 26 (0.4%) |

## Segmentation Methodology & Rules

1. **Qualifying Purchase Events:** Only invoices with confirmed positive product sales (`product_sales > 0`), strictly positive quantities, valid customer IDs, and non-cancellation status increment purchase frequency. Charge-only invoices (postage, bank fees) do not count as purchases.
2. **Multi-line Invoice Aggregation:** Aggregation is performed at the unique invoice ID grain. Multi-line orders never inflate purchase frequency.
3. **Same-Day Order Handling:** Each distinct invoice represents a separate customer order transaction (`frequency`). Daily cadence is tracked independently via `distinct_purchase_days`.
4. **Deterministic Frequency Scoring:** Discrete binning ensures that all 1-time buyers receive score 1, 2-order buyers score 2, 3-4 orders score 3, 5-8 orders score 4, and 9+ orders score 5, completely eliminating arbitrary tie-breaking.
5. **Negative Net Spend Isolation:** Customers with net cumulative spend <= £0.00 due to returns are segregated into a dedicated `Negative or Zero Spend` segment.
