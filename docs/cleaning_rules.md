# RetenSight Cleaning Rules and Methodology

This document outlines the exact business rules, data-quality criteria, transaction classifications, and duplicate resolution logic applied in the RetenSight ingestion and cleaning pipeline.

## 1. Workbook Ingestion & Schema Normalization

1. **Sheet Ingestion**: The raw workbook (`online_retail_II.xlsx`) contains two sheets: `Year 2009-2010` and `Year 2010-2011`. The pipeline verifies sheet presence and header conformity (`Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`).
2. **Provenance Tracking**: Each ingested record retains `source_sheet` and `source_row_num` (1-indexed row number in the original Excel file) to preserve full data lineage.
3. **Data Type Casting**:
   - `invoice`: Cleaned string, stripped of leading/trailing whitespace.
   - `stock_code`: Cleaned uppercase string.
   - `description`: Cleaned string; empty if missing.
   - `quantity`: Signed 64-bit integer (`int64`).
   - `price`: 64-bit float (`float64`).
   - `invoice_date`: Parsed UTC/naive timestamp (`datetime64[ns]`).
   - `customer_id`: Nullable integer (`Int64`).
   - `country`: Cleaned string.

## 2. Cross-Sheet Duplicate Resolution

### Background
The UCI Online Retail II dataset exhibits a known date overlap between `Year 2009-2010` (ends 2010-12-09 20:01:00) and `Year 2010-2011` (starts 2010-12-01 08:26:00). All rows in the overlap period were duplicated into the second sheet.

### Strict 1-to-1 Matching Protocol
- Duplicate elimination applies **only across sheets**, never within a sheet. Legitimate repeated purchases or identical multi-item orders within the same sheet are strictly preserved.
- A row in Sheet 2 is identified as a cross-sheet duplicate if and only if there exists an identical row in Sheet 1 across all 8 raw columns, matching on the exact within-sheet occurrence multiplicity index (`occurrence_id = cumcount() + 1`).
- Missing values (e.g. `NaN` in `Customer ID` or `Description`) are treated as identical across sheets (`NaN == NaN`).
- Exactly 22,523 rows in Sheet 2 match Sheet 1 under this rule and are removed, leaving 1,044,848 unique records across the two years.

## 3. Transaction Categorization & Cleaning Rules

No rows are silently discarded. Instead, each retained record is categorized and flagged:

1. **Cancellations / Returns (`cancellation`)**:
   - Invoices beginning with `C` or `c` indicate cancellations or returns (19,165 records total, -£1,465,303.66).
   - Quantity is almost universally negative (`quantity < 0`), representing stock returned.
   - One observed exception exists in the raw data (`C496350`, a manual line with quantity 1, price £373.57, and line total +£373.57). Per pipeline rules, this line is preserved at its observed value, classified under `cancellation`, and flagged with `has_positive_cancellation_line` on the invoice.
2. **Bad Debt Adjustments (`bad_debt_adjustment`)**:
   - Invoices beginning with `A` (6 records in total) represent company-wide accounting adjustments ("Adjust bad debt", StockCode `B`).
   - 5 rows have negative unit price (`Price < 0`, `Quantity = 1`, total -£158,676.14); 1 row has positive unit price (`Price > 0`, `Quantity = 1`, invoice `A563185`, value +£11,062.06).
   - Net bad-debt total is -£147,614.08. All have missing customer IDs. Excluded from customer analytics but tracked in financial reconciliation.
3. **Inventory Adjustments (`inventory_adjustment`)**:
   - Records with `Price == 0.0` and missing `Customer ID` (5,954 records total).
   - Descriptions include warehouse remarks like `"damages"`, `"lost"`, `"check"`, `"? "`, `"thrown away"`, `"damaged"`.
   - When `Quantity < 0` (3,393 records), these represent warehouse shrinkage/loss write-offs.
   - When `Quantity > 0` (2,561 records), these represent warehouse inventory reconciliations / found goods.
   - Excluded from commercial customer analytics; tracked in audit reports.
4. **Promotional Freebies (`promotional_freebie`)**:
   - Records with `Price == 0.0` where `Customer ID` is populated (70 records).
   - Quantity is positive (`Quantity > 0`). These represent complimentary promotional products included with customer orders.
   - Retained in the full cleaned transactions table and audit, but excluded from the commercial/model-ready customer extract so they cannot act as false positive purchase signals.
5. **Special Commercial Charges (`special_commercial_charge`)**:
   - Commercial line items with `Quantity > 0` and `Price > 0` using recognized non-merchandise stock codes (`POST`, `DOT`, `M`, `BANK CHARGES`, `AMAZONFEE`, `ADJUST`, etc.).
   - 4,228 records total, contributing £806,317.23 to gross commercial sales.
   - These charges contribute to total invoice spend and customer monetary value (RFM), but are distinguished from ordinary product merchandise so downstream product-affinity or basket analysis can isolate physical products.
6. **Standard Product Sales (`standard_product_sale`)**:
   - Invoices without `C` or `A` prefix, where `Quantity > 0`, `Price > 0`, and stock code is a physical merchandise item.
   - 1,015,425 records total, contributing £19,716,362.61 to gross sales.

## 4. Financial Definitions & Reconciliation

- **Line Total**: `line_total = quantity * price`.
- **Gross Product Sales**: Sum of `standard_product_sale` line totals (£19,716,362.61).
- **Special Commercial Charges**: Sum of `special_commercial_charge` line totals (£806,317.23).
- **Total Gross Commercial Sales**: Gross Product Sales + Special Commercial Charges (£20,522,679.84).
- **Cancellations / Refunds**: Sum of all cancellation-coded line totals (-£1,465,303.66).
- **Net Commercial Value (before bad debt)**: Gross Commercial Sales + Cancellations (£19,057,376.18).
- **Bad Debt Adjustments**: Sum of accounting debt adjustments (-£147,614.08).
- **All Transactions Net Value (after bad debt)**: Net Commercial Value + Bad Debt Adjustments (£18,909,762.10).
- Every transaction line and penny reconciles across transactions and invoice components within £0.01 tolerance.

## 5. Customer Modeling Readiness

- **Total Customer-Attributed Transactions**: 809,561 rows (791,045 positive sales + 18,446 cancellations + 70 promotional freebies).
- **Customer Commercial-Ready Transactions (`is_commercial_customer_ready`)**: Exactly **809,491 rows** (791,045 positive sales + 18,446 cancellations).
  - Promotional freebies (70 rows) are excluded from the model-ready extract because zero-price giveaway items do not represent commercial repeat-purchase intent.
  - Cancellations (18,446 rows) are preserved as a distinct behavioral category.

## 6. Invoice Grain Aggregation

- **Grain**: Exactly 1 row per unique `Invoice` code (53,628 unique invoices).
- **Dates**: Earliest timestamp `min(InvoiceDate)` across lines in the invoice.
- **Financial Components**: Aggregated strictly by transaction category, not by line total sign:
  - `product_sales`: Sum of line totals for `standard_product_sale`.
  - `special_charges`: Sum of line totals for `special_commercial_charge`.
  - `gross_sales`: `product_sales + special_charges`.
  - `cancellation_value`: Sum of line totals for `cancellation`.
  - `bad_debt_value`: Sum of line totals for `bad_debt_adjustment`.
  - `net_value`: `gross_sales + cancellation_value + bad_debt_value`.
- **Anomaly Detection**: `has_positive_cancellation_line` explicitly flags invoices where a cancellation-coded invoice contains a positive line (e.g. `C496350`).
