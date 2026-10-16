# RetenSight — Data Cleaning and Reconciliation Audit Report

RetenSight checks row counts and financial totals as data moves from the workbook to invoice and customer tables.

## Data volume

| Measure | Result |
|---|---:|
| Rows ingested | 1,067,371 |
| Verified cross-sheet copies removed | 22,523 |
| Rows retained | 1,044,848 |
| Customer-attributed rows | 809,561 |
| Customer commercial-ready rows | 809,491 |
| Unique invoices | 53,628 |
| Customers with qualifying purchase history | 5,942 |

## Financial reconciliation

| Measure | Company-wide value |
|---|---:|
| Gross Product Sales | £19,716,362.61 |
| Special Commercial Charges | £806,317.23 |
| Gross commercial sales | £20,522,679.84 |
| Cancellations and returns | -£1,465,303.66 |
| Net commercial value before bad debt | £19,057,376.18 |
| Bad-debt adjustments | -£147,614.08 |
| Net invoice value after bad debt | £18,909,762.10 |

Company-wide totals include unattributed transactions. Customer commercial net spend is a separate measure; it excludes administrative settlements and bad debt.

## Integrity checks

| Check | Result |
|---|---|
| Raw rows minus verified duplicates equals retained rows | PASSED [✓] |
| Transaction lines reconcile to invoice line counts | Passed |
| Transaction quantities reconcile to invoice quantities | Passed |
| Product sales reconcile | Passed |
| Special charges reconcile | Passed |
| Cancellations reconcile | Passed |
| Bad-debt value reconciles | Passed |
| Company net value reconciles to invoice totals | Passed |
| Commercial value plus bad debt reconciles to all-in net value | Passed |
| Customer commercial-ready row count reconciles | Passed |

## Cleaning notes

- Only confirmed copies duplicated between the two sheets are removed. Repeated rows within a sheet are preserved.
- Transaction lines keep their category and sign so sales, returns and adjustments can be reconciled.
- Free promotional items remain in the cleaned data but are excluded from the customer commercial-ready extract.
- Administrative settlements and bad debt remain in the accounting audit but are not treated as customer purchases.

