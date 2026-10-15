# RetenSight Cleaning Rules and Methodology

This document outlines the exact business rules, data-quality criteria, and duplicate resolution logic applied in the RetenSight ingestion and cleaning pipeline.

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

1. **Cancellations / Returns (`is_cancellation`)**:
   - Invoices beginning with `C` or `c` indicate cancellations or returns.
   - Quantity is negative (`quantity < 0`), representing stock returned.
   - Line total is negative (`quantity * price`), representing refunded gross revenue.
   - Exactly 1 exception exists in the raw data (`C496350`, manual line with positive quantity 1); it is classified as a cancellation per invoice designation.
2. **Bad Debt Adjustments (`is_bad_debt`)**:
   - Invoices beginning with `A` (6 records in total) represent company-wide accounting adjustments ("Adjust bad debt", StockCode `B`).
   - 5 rows have negative unit price (`Price < 0`, `Quantity = 1`); 1 row has positive unit price (`Price > 0`, `Quantity = 1`).
   - All have missing customer IDs. Excluded from customer analytics but tracked in financial reconciliation.
3. **Inventory Adjustments (`inventory_adjustment`)**:
   - Records with `Price == 0.0` and missing `Customer ID`.
   - Descriptions include audit remarks like `"damages"`, `"lost"`, `"check"`, `"? "`, `"thrown away"`, `"damaged"`.
   - When `Quantity < 0` (3,393 records), these represent warehouse shrinkage/loss write-offs.
   - When `Quantity > 0` (2,561 records), these represent warehouse inventory reconciliations / found goods.
   - Excluded from commercial customer analytics; tracked in audit reports.
4. **Promotional Freebies (`promotional_freebie`)**:
   - Records with `Price == 0.0` where `Customer ID` is populated (70 records).
   - Quantity is positive (`Quantity > 0`). These represent complimentary promotional products included with customer orders.
5. **Standard Commercial Sales (`standard_sale`)**:
   - Invoices without `C` or `A` prefix, where `Quantity > 0` and `Price > 0`.
   - 1,019,653 records total:
     - 791,045 customer-attributed sales records (77.6% of sales).
     - 228,608 unattributed guest sales records (22.4% of sales).

## 4. Financial Calculations & Reconciliation

- **Line Value**: `line_total = quantity * price`.
- **Gross Positive Sales**: Sum of `line_total` for all `standard_sale` rows (£20,522,679.86).
- **Cancellations / Returns**: Sum of `line_total` for all `cancellation` rows (-£1,465,303.66).
- **Bad Debt Adjustments**: Sum of `line_total` for `bad_debt` rows (-£147,614.08).
- **Net Revenue**: $\text{Gross Sales} + \text{Cancellations} + \text{Bad Debt} = £18,909,762.12$.
- Every transaction line and penny reconciles across transactions, invoices, and customer aggregates.

## 5. Invoice Grain Aggregation

- Grain: Exactly 1 row per unique `Invoice` code (53,628 invoices in total).
- Dates: Earliest timestamp `min(InvoiceDate)` across lines in the invoice.
- Customer ID: Exactly 1 customer per invoice (0 invoices have conflicting customer IDs).
- Country: Exactly 1 country per invoice (0 invoices have conflicting countries).
- Mixed Signs: 0 invoices have mixed positive and negative quantities.
- Financials:
  - `gross_sales`: Sum of positive line totals (£).
  - `cancellation_value`: Sum of negative line totals (£).
  - `net_value`: `gross_sales + cancellation_value`.
