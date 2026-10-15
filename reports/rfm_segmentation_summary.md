# RetenSight — Customer RFM Analytics & Segmentation Summary

## Executive Summary

This report details customer-level RFM features, monetary component reconciliation, 
deterministic single-source-of-truth 125-cell CRM segmentation, merchandise and commercial AOV, 
and observed 90-day repeat-purchase rates across chronological evaluation cutoffs for the UCI Online Retail II dataset.

## Cutoff Overview & Observed 90-Day Repeat-Purchase Rates

| Evaluation Cutoff | Target Observation Window | Eligible Customers | Mean Recency (Days) | Mean Frequency | Mean Merchandise AOV (£) | Mean Commercial AOV (£) | Total Net Commercial Spend (£) | 90-Day Repeat Buyers | Observed Repeat Rate (%) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2010-12-09` | 2010-12-10 to 2011-03-09 23:59:59 (90 days) | 4,286 | 89.6 | 4.43 | £375.67 | £378.42 | £8,431,965.25 | 1,317 | 30.73% |
| `2011-06-10` | 2011-06-11 to 2011-09-08 23:59:59 (90 days) | 4,952 | 170.3 | 5.27 | £372.20 | £375.37 | £11,470,023.08 | 1,586 | 32.03% |
| `2011-09-09` | 2011-09-10 to 2011-12-08 23:59:59 (90 days) | 5,257 | 205.9 | 5.71 | £368.00 | £371.42 | £13,259,983.01 | 2,287 | 43.50% |
| `2011-12-09` | Unobserved (Dataset ends at 2011-12-09 12:50:00) | 5,853 | 199.2 | 6.25 | £382.95 | £386.62 | £16,432,195.66 | N/A | Unobserved (Marked <NA>) |

## Cross-Cutoff CRM Segment Distribution (125-Cell Single Source of Truth)

| CRM Segment | `2010-12-09` Count (%) | `2011-06-10` Count (%) | `2011-09-09` Count (%) | `2011-12-09` Count (%) |
| :--- | ---: | ---: | ---: | ---: |
| **Champions** | 786 (18.3%) | 1,042 (21.0%) | 1,139 (21.7%) | 1,257 (21.5%) |
| **Loyal Customers** | 609 (14.2%) | 762 (15.4%) | 787 (15.0%) | 937 (16.0%) |
| **Potential Loyalists** | 407 (9.5%) | 388 (7.8%) | 418 (8.0%) | 507 (8.7%) |
| **New Customers** | 217 (5.1%) | 223 (4.5%) | 205 (3.9%) | 207 (3.5%) |
| **Promising** | 228 (5.3%) | 187 (3.8%) | 193 (3.7%) | 211 (3.6%) |
| **About To Sleep** | 810 (18.9%) | 999 (20.2%) | 1,053 (20.0%) | 1,088 (18.6%) |
| **At Risk** | 332 (7.8%) | 386 (7.8%) | 407 (7.7%) | 458 (7.8%) |
| **Can't Lose Them** | 157 (3.7%) | 144 (2.9%) | 176 (3.4%) | 215 (3.7%) |
| **Hibernating** | 159 (3.7%) | 201 (4.1%) | 224 (4.3%) | 253 (4.3%) |
| **Lost** | 562 (13.1%) | 600 (12.1%) | 634 (12.1%) | 695 (11.9%) |
| **Negative or Zero Spend** | 19 (0.4%) | 20 (0.4%) | 21 (0.4%) | 25 (0.4%) |

## Explicit Monetary-Aware Decision Table (125 Cells + Negative Spend)

The RFM segmentation scheme deterministically maps every possible combination of `(r_score, f_score, m_score)` 
plus negative net spend to 11 mutually exclusive, exhaustive business categories. The complete 126-row decision table 
is published in machine-readable form at `reports/crm_segment_decision_table.csv` and `reports/crm_segment_decision_table.json`.

| CRM Segment | Cell Count | Criteria Summary | Business Rationale & Core Action |
| :--- | ---: | :--- | :--- |
| **Champions** | 8 | `R in [4, 5]`, `F in [4, 5]`, `M in [4, 5]` | Top-tier VIP concierge outreach, early product access, executive appreciation. |
| **Loyal Customers** | 21 | (`R in [4, 5]`, `F in [4, 5]`, `M in [2, 3]`) or (`R == 3`, `F in [4, 5]`, `M in [3, 4, 5]`) or (`R in [3, 4, 5]`, `F == 3`, `M in [4, 5]`) or (`R == 3`, `F == 3`, `M == 3`) | Membership loyalty rewards, category cross-sell, automated reorder reminders. |
| **Potential Loyalists** | 12 | `R in [4, 5]`, `F in [2, 3]`, `M in [2, 3, 4, 5]` | Category cross-sell, second-tier order bundles, loyalty point incentives. |
| **New Customers** | 4 | `R in [4, 5]`, `F == 1`, `M in [1, 2]` | Dedicated onboarding sequence, welcome-back second order discount. |
| **Promising** | 20 | (`R in [4, 5]`, `F == 1`, `M in [3, 4, 5]`) or (`R in [4, 5]`, `F in [2, 3, 4, 5]`, `M == 1`) or (`R == 3`, `F in [1, 2]`, `M in [3, 4, 5]`) | Incentives to increase basket size and establish regular purchasing cadence. |
| **Can't Lose Them** | 10 | (`R in [1, 2]`, `F in [4, 5]`, `M in [4, 5]`) or (`R in [1, 2]`, `F == 3`, `M == 5`) | Highest priority win-back campaigns, bespoke commercial terms, direct executive outreach. |
| **At Risk** | 26 | (`R in [1, 2]`, `F in [4, 5]`, `M in [2, 3]`) or (`R == 2`, `F in [4, 5]`, `M == 1`) or (`R in [1, 2]`, `F == 3`, `M in [3, 4]`) or (`R in [1, 2]`, `F == 2`, `M in [4, 5]`) or (`R in [1, 2]`, `F == 1`, `M in [4, 5]`) or (`R == 3`, `F in [4, 5]`, `M in [1, 2]`) | Targeted re-engagement campaigns, personalized catalog offers, renewal discounts. |
| **About To Sleep** | 14 | (`R == 2`, `F in [1, 2]`, `M in [1, 2, 3]`) or (`R == 2`, `F == 3`, `M in [1, 2]`) or (`R == 3`, `F in [1, 2]`, `M in [1, 2]`) or (`R == 3`, `F == 3`, `M in [1, 2]`) | Gentle re-activation reminders before dormancy; low-friction seasonal promotions. |
| **Hibernating** | 7 | (`R == 1`, `F in [2, 3]`, `M in [1, 2, 3]`) or (`R == 1`, `F in [4, 5]`, `M == 1`) | Automated low-cost email drip campaigns; seasonal clearance announcements. |
| **Lost** | 3 | `R == 1`, `F == 1`, `M in [1, 2, 3]` | Deprioritized from high-touch CRM; archive or broad brand awareness only. |
| **Negative or Zero Spend** | 1 | `net_commercial_spend <= 0.0` or `M == 0` | Audit return reasons, inspect product defect reports, review trade concessions. |

## Customer Monetary Value Reconciliation & Sensitivity Analysis

### 1. Independently Aggregated Commercial Components
- **Merchandise Sales (`product_sales`):** £17,137,712.98 across 788,464 non-cancellation product lines.
- **Merchandise Returns (`merchandise_returns_value`):** -£713,343.75 across 17,652 product return lines.
- **Shipping Charges (`shipping_value`):** +£122,244.87 across customer shipping entries (`POST`, `DOT`).
- **Commercial Discounts (`discount_value`):** -£12,785.34 across trade discount entries (`D`).
- **Manual Commercial Adjustments (`manual_value`):** -£185,325.48 across manual entries (`M`).
- **Reconciliation Residual:** Exactly **£0.00** across all customer accounts.
- **Primary Customer Commercial Net Spend:** **£16,348,503.28** (sum of above 5 components).

### 2. Company Accounting Ledger & Administrative Settlements
- **Customer Administrative Settlements:** -£4,834.26 (`CRUK`, `BANK CHARGES`, `ADJUST`, `ADJUST2`).
- **Customer Account Balance:** **£16,343,669.02** (£16,348,503.28 + (-£4,834.26)).
- **Whole-Company Accounting Net Value:** **£18,909,762.10** (including £2,566,093.08 unattributed revenue).

### 3. Administrative Settlements Sensitivity Analysis
- **Whole Dataset Population (5,942 customer accounts):**
  - Accounts with any administrative transaction: **74**
  - Accounts with non-zero net administrative settlement: **69** (total net value: -£4,834.26)
  - Accounts with net zero administrative settlement: **5** (transactions cancel out exactly to £0.00)
- **Final RFM Snapshot (2011-12-09, 5,853 qualifying customers):**
  - Qualifying accounts with any administrative transaction: **53**
  - Qualifying accounts with non-zero net administrative settlement: **48**
  - Qualifying accounts with net zero administrative settlement: **5**
- **Excluded Accounts (21 accounts):**
  - 21 accounts with administrative transactions had 0 qualifying merchandise purchases (e.g. only cancellations or administrative adjustments) and are correctly excluded from repeat-purchase modeling.
