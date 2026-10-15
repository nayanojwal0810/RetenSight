# RetenSight Data Dictionary

This document defines the schemas and definitions for the UCI Online Retail II raw source data, the cleaned transaction-level dataset, and the invoice-level aggregate table produced by the RetenSight ingestion and cleaning pipeline.

## 1. Raw Workbook Schema

The source dataset is the UCI Online Retail II Excel workbook (`online_retail_II.xlsx`), consisting of two sheets:
- `Year 2009-2010` (525,461 data rows)
- `Year 2010-2011` (541,910 data rows)

Both sheets share the following 8 columns:

| Column Name | Raw Type in Excel | Description | Notes / Quality Issues |
| :--- | :--- | :--- | :--- |
| `Invoice` | integer or string | 6-digit invoice identifier; cancellations prefix with 'C'; bad debt adjustments prefix with 'A'. | Can be numeric or alphanumeric. |
| `StockCode` | integer or string | 5-digit product code or alphanumeric item code. | Contains non-product administrative codes (e.g., `POST`, `D`, `M`, `BANK CHARGES`, `AMAZONFEE`, `DOT`, `B`). |
| `Description` | string | Product or transaction description text. | Missing for several administrative adjustment records; text noise present. |
| `Quantity` | integer | Number of units per line item. | Negative for cancellations, returns, and inventory write-offs (e.g. damages, lost goods). |
| `InvoiceDate` | datetime | Timestamp of the transaction. | Recorded to minute precision. Sheets overlap from 2010-12-01 08:26:00 to 2010-12-09 20:01:00. |
| `Price` | float | Unit selling price in GBP (£). | Zero for inventory adjustments and free promotional gifts; negative for bad debt adjustments. |
| `Customer ID` | float / integer | 5-digit unique customer identifier. | Missing (`NaN`) for unattributed guest checkout orders and administrative adjustments. |
| `Country` | string | Name of the country where customer resides. | Categorical; predominantly `United Kingdom`. |

---

## 2. Cleaned Transaction Schema (`cleaned_transactions.parquet` / `.csv`)

Normalized, enriched, and classified transaction lines (1,044,848 rows after exact cross-sheet deduplication).

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `invoice` | `string` | Normalized, trimmed invoice code. |
| `stock_code` | `string` | Normalized uppercase stock code. |
| `description` | `string` | Normalized text description (empty string if missing). |
| `quantity` | `int64` | Transaction quantity (positive for sales, negative for cancellations/adjustments). |
| `invoice_date` | `timestamp[ns]` | Standardized transaction timestamp. |
| `price` | `float64` | Unit price in GBP (£). |
| `line_total` | `float64` | Total line value in GBP (`quantity * price`). |
| `customer_id` | `Int64` (nullable) | 5-digit integer customer identifier, or null if unattributed. |
| `country` | `string` | Normalized country name. |
| `source_sheet` | `string` | Source sheet provenance (`Year 2009-2010` or `Year 2010-2011`). |
| `source_row_num` | `int64` | 1-indexed row number within the source sheet. |
| `is_cancellation` | `bool` | True if invoice starts with 'C' (cancellation / return). |
| `is_bad_debt` | `bool` | True if invoice starts with 'A' (bad debt write-off). |
| `is_zero_price` | `bool` | True if unit price is exactly 0.0. |
| `is_negative_price` | `bool` | True if unit price is negative (< 0.0). |
| `has_customer_id` | `bool` | True if customer_id is present and non-null. |
| `is_special_code` | `bool` | True if stock_code is an administrative code (e.g. POST, D, M, BANK CHARGES, B). |
| `transaction_category` | `string` | Categorical classification: `standard_sale`, `cancellation`, `bad_debt_adjustment`, `inventory_adjustment`, or `promotional_freebie`. |
| `is_customer_analysis_ready` | `bool` | True for customer-attributed commercial transactions (sales and returns with valid customer ID). Excludes administrative adjustments. |

---

## 3. Invoice-Level Aggregate Schema (`invoice_aggregates.parquet` / `.csv`)

Summary table at invoice grain (53,628 unique invoices).

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `invoice` | `string` | Unique invoice identifier (Primary Key). |
| `invoice_date` | `timestamp[ns]` | Timestamp of the invoice (earliest line timestamp). |
| `customer_id` | `Int64` (nullable) | Customer identifier, or null if unattributed. |
| `country` | `string` | Country associated with the invoice. |
| `invoice_type` | `string` | Invoice classification: `customer_sale`, `customer_cancellation`, `unattributed_sale`, `unattributed_cancellation`, `inventory_adjustment`, or `bad_debt_adjustment`. |
| `has_customer_id` | `bool` | True if customer_id is present. |
| `is_cancellation` | `bool` | True if invoice starts with 'C'. |
| `line_count` | `int64` | Total number of line items on the invoice. |
| `total_quantity` | `int64` | Sum of all quantities on the invoice. |
| `gross_sales` | `float64` | Sum of line value for positive-quantity lines (£). |
| `cancellation_value` | `float64` | Sum of line value for negative-quantity lines (£). |
| `net_value` | `float64` | Net total invoice value (`gross_sales + cancellation_value`) (£). |
| `distinct_items` | `int64` | Number of distinct stock codes on the invoice. |
| `source_sheet` | `string` | Provenance sheet (`Year 2009-2010`, `Year 2010-2011`, or `mixed`). |
