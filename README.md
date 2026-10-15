# RetenSight

E-commerce CRM decision support for customer segmentation, repeat-purchase propensity, and explainable retention prioritization.

## Overview

RetenSight is an analytical decision-support system built upon transaction data from the UCI Online Retail II dataset (December 2009 – December 2011). The system aims to provide e-commerce retention teams with transparent customer intelligence, RFM segmentation, 90-day repeat-purchase propensity forecasting, and capacity-constrained CRM queue prioritization.

## Current Status

The data ingestion, schema validation, exact cross-sheet duplicate resolution, data-quality auditing, transaction classification, and invoice aggregation layers are implemented, tested, and validated on the complete two-year dataset.

### Key Dataset Reconciliation Summary

- **Raw Rows Ingested**: 1,067,371 rows across two sheets (`Year 2009-2010`: 525,461; `Year 2010-2011`: 541,910).
- **Exact Cross-Sheet Duplicates Removed**: 22,523 rows (from the December 1–9, 2010 overlap window). Legitimate same-sheet repeated purchases are strictly preserved.
- **Retained Transactions**: 1,044,848 rows (809,561 customer-attributed; 235,287 unattributed).
- **Unique Invoices**: 53,628 (36,975 customer sales; 7,901 customer cancellations; 4,962 unattributed sales; 391 unattributed cancellations; 3,393 inventory write-offs; 6 bad debt adjustments).
- **Distinct Valid Customers**: 5,942.
- **Gross Commercial Sales**: £20,522,679.84 (Attributed: £17,431,551.16; Unattributed: £3,091,128.68).
- **Cancellations / Returns**: -£1,465,303.66 (Attributed: -£1,087,882.14; Unattributed: -£377,421.52).
- **Bad Debt Adjustments**: -£147,614.08.
- **Net Commercial Revenue**: £18,909,762.10 (Reconciles exactly to invoice totals; discrepancy: £0.00).

Detailed reports and schemas are available in:
- [Data Dictionary](docs/data_dictionary.md)
- [Cleaning Rules and Methodology](docs/cleaning_rules.md)
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
