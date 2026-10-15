# RetenSight

E-commerce CRM decision support for customer segmentation, repeat-purchase propensity, and explainable retention prioritization.

## Overview

RetenSight is an analytical decision-support system built upon transaction data from the UCI Online Retail II dataset (December 2009 – December 2011). The system aims to provide e-commerce retention teams with transparent customer intelligence, RFM segmentation, 90-day repeat-purchase propensity forecasting, and capacity-constrained CRM queue prioritization.

## Current Status

The data ingestion, schema validation, exact cross-sheet duplicate resolution, data-quality auditing, transaction classification, invoice aggregation, special stock code audit, and customer-level RFM segmentation layers are fully implemented, tested, and validated on the complete two-year dataset.

### Key Dataset Reconciliation Summary

- **Raw Rows Ingested**: 1,067,371 rows across two sheets (`Year 2009-2010`: 525,461; `Year 2010-2011`: 541,910).
- **Exact Cross-Sheet Duplicates Removed**: 22,523 rows (from the December 1–9, 2010 overlap window). Legitimate same-sheet repeated purchases are strictly preserved.
- **Retained Transactions**: 1,044,848 rows (809,561 customer-attributed; 235,287 unattributed).
- **Unique Invoices**: 53,628 (36,975 customer sales; 7,901 customer cancellations; 4,962 unattributed sales; 391 unattributed cancellations; 3,393 inventory write-offs; 6 bad debt adjustments).
- **Gross Product Sales**: £19,716,362.61 (Ordinary merchandise items, including cushion pads).
- **Special Commercial Charges**: £806,317.23 (POST, DOT, M, BANK CHARGES, etc.).
- **Total Gross Commercial Sales**: £20,522,679.84 (Attributed: £17,431,551.16; Unattributed: £3,091,128.68).
- **Cancellations / Returns**: -£1,465,303.66 (Attributed: -£1,087,882.14; Unattributed: -£377,421.52).
- **Bad Debt Adjustments**: -£147,614.08.
- **All Transactions Net Value (Whole-Company Accounting)**: £18,909,762.10 (Reconciles exactly to invoice totals; discrepancy: £0.00).
- **Customer Account Ledger Total (5,942 customers)**: £16,343,669.02.
- **Customer Administrative Settlements (`CRUK`, `BANK CHARGES`, `ADJUST`, `ADJUST2`)**: -£4,834.26 (isolated from commercial spend).
- **Primary Customer Commercial Net Spend**: £16,348,503.28 (£16,343,669.02 − (-£4,834.26)).
- **Customer Modeling-Ready Transactions**: 809,491 rows (excludes 70 zero-revenue promotional freebies from the commercial extract).
- **Merchandise AOV & Commercial Order Value**: Conventional retail merchandise AOV is calculated strictly from qualifying catalog product sales ($\sum \text{qualifying\_merchandise\_sales} / \text{frequency}$). Commercial order value is also exposed inclusive of customer delivery surcharges. Changing non-merchandise administrative fees does not affect merchandise AOV.
- **Direct Return Aggregation & Zero Residual**: Merchandise returns (-£713,343.75 customer total) are directly aggregated from physical merchandise lines on cancellation invoices rather than calculated as a residual. The explicit customer reconciliation residual is identically £0.00 across all 5,942 customer accounts.
- **Single Source of Truth 125-Cell Decision Table**: All 125 $(R, F, M)$ quintile cells plus non-positive spend are deterministically mapped without cascading overlaps, exported as machine-readable reference tables in `reports/crm_segment_decision_table.json` and `reports/crm_segment_decision_table.csv`.
- **Customer RFM Snapshots**: Generated for 3 chronological evaluation cutoffs with fully observed 90-day forward windows (`2010-12-09`: 4,286 customers, 30.73% repeat rate; `2011-06-10`: 4,952 customers, 32.03% repeat rate; `2011-09-09`: 5,257 customers, 43.50% repeat rate) plus the full dataset end snapshot (`2011-12-09`: 5,853 customers; forward target unobserved `<NA>`).

Detailed reports and schemas are available in:
- [Customer RFM Feature Definitions & Segmentation](docs/rfm_feature_definitions.md)
- [Special Stock Code & Fee Audit](docs/special_stock_code_audit.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Cleaning Rules and Methodology](docs/cleaning_rules.md)
- [RFM Segmentation Summary Report](reports/rfm_segmentation_summary.md)
- [CRM Segment Decision Table (JSON)](reports/crm_segment_decision_table.json)
- [CRM Segment Decision Table (CSV)](reports/crm_segment_decision_table.csv)
- [Special Stock Code Audit Report](reports/special_stock_codes_audit.md)
- [Cleaning and Reconciliation Summary Report](reports/cleaning_and_reconciliation_summary.md)
- [Machine-Readable Audit JSON](reports/data_quality_audit.json)

---

## Installation

Ensure Python 3.10+ is installed. Clone the repository and install dependencies:

```bash
git clone https://github.com/nayanojwal0810/RetenSight.git
cd RetenSight
pip install -r requirements.txt
```

---

## Execution

Place the raw UCI Online Retail II workbook at `data/raw/online_retail_II.xlsx` (or pass an explicit path).

Run the complete pipeline:

```bash
python -m retensight.pipeline
```

Custom options:

```bash
python -m retensight.pipeline --input-path data/raw/online_retail_II.xlsx --output-dir data/processed --reports-dir reports
```

### Generated Outputs

- `data/processed/cleaned_transactions.parquet`: Full cleaned transaction dataset with classification flags (1,044,848 rows).
- `data/processed/customer_transactions.parquet`: Customer-attributed commercial transactions ready for downstream analytics (809,491 rows).
- `data/processed/invoice_aggregates.parquet` & `.csv`: Invoice grain table with financial and quantity aggregates (53,628 rows).
- `reports/data_quality_audit.json`: Machine-readable data-quality and financial reconciliation audit.
- `reports/cleaning_and_reconciliation_summary.md`: Human-readable audit report.

---

## Automated Tests

Run the unit test suite (fast, synthetic fixtures):

```bash
python -m pytest -v -m "not full_data"
```

Run the complete test suite including end-to-end full workbook verification:

```bash
python -m pytest -v
```

---

## Design Principles

- **Full Dataset Verification**: Real full-workbook execution without sampling or fabricated metrics.
- **Strict 1-to-1 Duplicate Matching**: Eliminates only verified cross-sheet duplicate copies in the overlap window, preserving within-sheet repeat purchases.
- **Zero Silent Data Loss**: All records are classified and accounted for in reconciliations.
- **Strict Invariant Checking**: Automated assertions ensure row count, quantity, and revenue reconciliation across transactions and invoices.
- **CPU-Only & Free**: Pure Python and open-source tooling; high performance parsing via Calamine and Parquet storage.
- **Transparent Attribution**: Cites and acknowledges prior art, including reference methods from [ecommerce-churn-clv-prediction](https://github.com/ruturajdixit99/ecommerce-churn-clv-prediction).
