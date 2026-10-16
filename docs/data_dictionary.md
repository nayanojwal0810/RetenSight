# Data Dictionary

RetenSight uses the UCI Online Retail II workbook and creates cleaned transaction, invoice, customer and reporting tables. This page describes the fields most useful for understanding the project; the code and generated CSV/JSON files contain the full schemas.

## Source workbook

The raw workbook has these eight columns:

| Source column | Meaning |
|---|---|
| `Invoice` | Invoice identifier. Codes beginning with `C` mark cancellations; codes beginning with `A` mark bad-debt adjustments. |
| `StockCode` | Product or transaction code. Some codes represent postage, discounts or accounting entries, not products. |
| `Description` | Product or transaction description. It may be missing for adjustments. |
| `Quantity` | Number of units. Negative values can represent returns or adjustments. |
| `InvoiceDate` | Transaction timestamp. |
| `Price` | Unit price in pounds sterling. |
| `Customer ID` | Customer identifier; missing for unattributed transactions. |
| `Country` | Customer country. |

## Main output tables

| File | One row represents | Main use |
|---|---|---|
| `cleaned_transactions.parquet` | One cleaned transaction line | Audits and downstream aggregation |
| `customer_transactions.parquet` | One customer-attributed commercial transaction line | Customer-level analysis |
| `invoice_aggregates.parquet` | One invoice | Financial reconciliation and purchase-event logic |
| `rfm_snapshot_YYYYMMDD.parquet` | One customer at one scoring date | RFM features, segments and model inputs |
| `rfm_summary_all_cutoffs.parquet` | One customer-snapshot record | Cross-date analysis |
| `reports/data_quality_audit.json` | One audit report | Machine-readable counts and reconciliation checks |
| `reports/rfm_segmentation_summary.json` | One segmentation summary | Customer counts and segment distribution |
| `reports/repeat_purchase_model_metrics.csv` | One model/cohort result | Model evaluation |
| `reports/crm_queue_policy_comparison.csv` | One model/cohort/capacity/policy result | CRM queue trade-offs |

Processed parquet files are generated locally and are not required to launch the hosted dashboard.

## Important fields

| Field | Meaning |
|---|---|
| `line_total` | `quantity × price`, in GBP |
| `transaction_category` | Classification such as product sale, commercial charge, cancellation, inventory adjustment or freebie |
| `is_commercial_customer_ready` | True for customer-attributed commercial lines retained for customer analysis; false for free promotional items and excluded records |
| `product_sales` | Product sales on an invoice, separate from service charges |
| `special_charges` | Commercial fees such as shipping or manual charges |
| `net_value` | Invoice value including cancellations and bad-debt adjustments, as defined by the invoice aggregation |
| `net_commercial_spend` | Customer commercial net spend excluding administrative settlements and bad debt |
| `recency_days` | Days since the most recent qualifying purchase |
| `frequency` | Number of distinct qualifying purchase invoices |
| `r_score`, `f_score`, `m_score` | RFM scores for recency, frequency and monetary value |
| `segment` | Customer segment derived from the RFM scores and spend rules |
| `target_repeat_purchase_90d` | 1 if the customer makes a qualifying purchase in the next 90 days; 0 if not; missing if the window is not observed |
| `is_target_window_observed` | Whether the full forward 90-day period is available |

## Financial terms

- **Company-wide net invoice value:** company-level commercial value after returns and bad debt, including unattributed business.
- **Customer commercial net spend:** customer-attributed commercial sales after commercial adjustments and returns, excluding administrative settlements and bad debt.
- **Historical queue spend:** historical customer commercial spend associated with customers selected by a contact strategy. It is not revenue saved or profit.

See [cleaning rules](cleaning_rules.md) and [RFM definitions](rfm_feature_definitions.md) for the treatment rules.
