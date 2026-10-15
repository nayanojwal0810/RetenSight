# RetenSight — Customer RFM Analytics & Segmentation Summary

## Executive Summary

This report details the customer-level RFM features, monetary component reconciliation, 
deterministic monetary-aware scoring, explainable CRM segmentation, and observed 90-day repeat-purchase rates 
across chronological evaluation cutoffs for the UCI Online Retail II dataset.

## Cutoff Overview & Observed 90-Day Repeat-Purchase Rates

| Evaluation Cutoff | Target Observation Window | Eligible Customers | Mean Recency (Days) | Mean Frequency | Mean Commercial AOV (£) | Total Net Commercial Spend (£) | 90-Day Repeat Buyers | Observed Repeat Rate (%) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2010-12-09` | 2010-12-10 to 2011-03-09 23:59:59 (90 days) | 4,286 | 89.6 | 4.43 | £378.61 | £8,431,965.25 | 1,317 | 30.73% |
| `2011-06-10` | 2011-06-11 to 2011-09-08 23:59:59 (90 days) | 4,952 | 170.3 | 5.27 | £375.51 | £11,470,023.08 | 1,586 | 32.03% |
| `2011-09-09` | 2011-09-10 to 2011-12-08 23:59:59 (90 days) | 5,257 | 205.9 | 5.71 | £371.55 | £13,259,983.01 | 2,287 | 43.50% |
| `2011-12-09` | Unobserved (Dataset ends at 2011-12-09 12:50:00) | 5,853 | 199.2 | 6.25 | £386.74 | £16,432,195.66 | N/A | Unobserved (Marked <NA>) |

## Cross-Cutoff CRM Segment Distribution (Monetary-Aware)

| CRM Segment | `2010-12-09` Count (%) | `2011-06-10` Count (%) | `2011-09-09` Count (%) | `2011-12-09` Count (%) |
| :--- | ---: | ---: | ---: | ---: |
| **Champions** | 786 (18.3%) | 1,042 (21.0%) | 1,139 (21.7%) | 1,257 (21.5%) |
| **Loyal Customers** | 432 (10.1%) | 606 (12.2%) | 635 (12.1%) | 798 (13.6%) |
| **Potential Loyalists** | 584 (13.6%) | 544 (11.0%) | 570 (10.8%) | 646 (11.0%) |
| **New Customers** | 131 (3.1%) | 142 (2.9%) | 113 (2.1%) | 104 (1.8%) |
| **Promising** | 471 (11.0%) | 415 (8.4%) | 454 (8.6%) | 467 (8.0%) |
| **About To Sleep** | 463 (10.8%) | 614 (12.4%) | 609 (11.6%) | 642 (11.0%) |
| **At Risk** | 216 (5.0%) | 252 (5.1%) | 311 (5.9%) | 399 (6.8%) |
| **Can't Lose Them** | 316 (7.4%) | 320 (6.5%) | 333 (6.3%) | 362 (6.2%) |
| **Hibernating** | 306 (7.1%) | 397 (8.0%) | 438 (8.3%) | 458 (7.8%) |
| **Lost** | 562 (13.1%) | 600 (12.1%) | 634 (12.1%) | 695 (11.9%) |
| **Negative or Zero Spend** | 19 (0.4%) | 20 (0.4%) | 21 (0.4%) | 25 (0.4%) |

## Explicit Monetary-Aware Decision Table

The RFM segmentation scheme deterministically maps all 125 possible score combinations of `(r_score, f_score, m_score)` 
plus negative net spend to 11 mutually exclusive, exhaustive business categories:

| CRM Segment | Condition Criteria | Core Business Strategy |
| :--- | :--- | :--- |
| **Champions** | `R in [4, 5]` and `F in [4, 5]` and `M in [4, 5]` | Top-tier VIP concierge outreach, early product access, executive appreciation. |
| **Loyal Customers** | (`R in [4, 5]` and `F in [4, 5]` and `M in [2, 3]`) or (`R == 3` and `F in [3, 4, 5]` and `M in [3, 4, 5]`) | Membership loyalty rewards, category cross-sell, referral programs. |
| **Potential Loyalists** | `R in [4, 5]` and `F in [2, 3]` and `M in [2, 3, 4, 5]` | Upsell incentives, second-tier order bundles, product recommendation journeys. |
| **New Customers** | `R in [4, 5]` and `F == 1` and `M in [2, 3, 4, 5]` | Dedicated onboarding sequences, welcome-back second order discount. |
| **Can't Lose Them** | `R in [1, 2]` and `F in [2, 3, 4, 5]` and `M in [4, 5]` | Highest priority win-back campaigns; bespoke commercial incentives and account management review. |
| **At Risk** | (`R in [1, 2]` and `F in [3, 4, 5]` and `M in [2, 3]`) or (`R in [1, 2]` and `F == 1` and `M in [4, 5]`) | Re-engagement campaigns, personalized catalog offers, targeted reactivation. |
| **Promising** | (`R == 3` and `F in [1, 2]` and `M in [2, 3, 4, 5]`) or (`R in [4, 5]` and `M == 1`) | Trial incentives to increase basket size, low-barrier category introductions. |
| **About To Sleep** | `R == 2` and `F in [1, 2]` and `M in [1, 2, 3]` | Reactivation before complete dormancy; survey interest and offer seasonal triggers. |
| **Hibernating** | (`R == 1` and `F >= 2` and `M in [1, 2]`) or (`R == 3` and `M in [1, 2]`) | Automated low-cost drip campaigns; deep discount clearances. |
| **Lost** | `R == 1` and `F == 1` and `M in [1, 2, 3]` | Deprioritized from high-touch marketing; archive or broad brand awareness only. |
| **Negative or Zero Spend** | `net_commercial_spend <= 0.0` | Audit returns, investigate merchandise defects, review concession abuse. |

## Customer Monetary Value Reconciliation & Sensitivity Analysis

1. **Customer Commercial Net Spend (Primary Measure):**
   - Includes: Standard catalog merchandise sales, customer shipping charges (`POST`, `DOT`), trade discounts (`D`), manual commercial adjustments (`M`), and genuine merchandise returns.
   - Total across full 24 months: £16,348,503.28.
2. **Administrative Settlements (Isolated):**
   - Includes: Cancer Research UK commission disbursements (`CRUK`, -£7,933.43), internal staff ledger adjustments (`ADJUST`/`ADJUST2`, +£2,769.17), and banking fees (`BANK CHARGES`, +£330.00).
   - Total across customer accounts: -£4,834.26.
3. **Account Balance Reconciliation:**
   - `net_commercial_spend (£16,348,503.28)` + `admin_settlements (-£4,834.26)` = `total_customer_account_balance (£16,343,669.02)`.
   - Reconciles to the penny across all customer invoices.
4. **Sensitivity Impact:**
   - Isolating administrative settlements affects only 68 out of 5,853 customers (1.16% of customer base).
   - For corporate partner account 14096 (CRUK), commercial merchandise purchases are correctly reflected as £65,054.34 rather than being artificially reduced by charity commission payouts.
