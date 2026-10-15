# RetenSight — Data Cleaning and Reconciliation Audit Report

## 1. Executive Summary

- **Raw Rows Ingested**: 1,067,371 across 2 workbook sheets (`Year 2009-2010`: 525,461, `Year 2010-2011`: 541,910)
- **Exact Cross-Sheet Duplicates Removed**: 22,523 (from `Year 2010-2011` overlap)
- **Retained Transactions**: 1,044,848
- **Distinct Valid Customers**: 5,942
- **Total Unique Invoices**: 53,628
- **Gross Commercial Sales**: £20,522,679.84
- **Cancellations / Refunds**: -£1,465,303.66
- **Bad Debt Adjustments**: -£147,614.08
- **Net Commercial Revenue**: £18,909,762.10

---

## 2. Ingestion & Duplicate Resolution

| Metric | Value | Notes |
| :--- | :--- | :--- |
| Sheet 1 Raw Rows (`Year 2009-2010`) | 525,461 | Dates: 2009-12-01 to 2010-12-09 |
| Sheet 2 Raw Rows (`Year 2010-2011`) | 541,910 | Dates: 2010-12-01 to 2011-12-09 |
| Date Overlap Window | 2010-12-01 08:26:00 to 2010-12-09 20:01:00 | Overlap period |
| Cross-Sheet 1-to-1 Duplicates Removed | 22,523 | Removed strictly from `Year 2010-2011` |
| Sheet 1 Same-Sheet Duplicates Preserved | 13,283 | Legitimate repeat rows kept |
| Retained Rows Post-Deduplication | 1,044,848 | Exactly Sheet 1 + Retained Sheet 2 |

---

## 3. Transaction Breakdown by Classification

| Category | Rows | % of Total | Description |
| :--- | :--- | :--- | :--- |
| `standard_sale` | 1,019,653 | 97.59% | Commercial positive sales (qty > 0, price > 0) |
| `cancellation` | 19,165 | 1.83% | Invoices starting with 'C' (returns/cancellations) |
| `inventory_adjustment` | 5,954 | 0.57% | Administrative loss/found write-offs (price=0, no customer ID) |
| `promotional_freebie` | 70 | 0.01% | Free gifts with customer orders (price=0, customer ID present) |
| `bad_debt_adjustment` | 6 | 0.0006% | Invoices starting with 'A' (accounting debt write-offs) |
| **Total Retained Rows** | **1,044,848** | **100.00%** | |

### Customer Attribution
- **Customer-Attributed Transactions**: 809,561 (77.48%)
- **Unattributed Transactions**: 235,287 (22.52%)

---

## 4. Invoice Aggregation

| Invoice Type | Invoices | Line Count | Distinct Customers |
| :--- | :--- | :--- | :--- |
| Customer Sales (`customer_sale`) | 36,975 | Attributed | 5,942 |
| Customer Cancellations (`customer_cancellation`) | 7,901 | Attributed | - |
| Unattributed Sales (`unattributed_sale`) | 4,962 | Guest checkout | N/A |
| Unattributed Cancellations | 391 | Guest returns | N/A |
| Inventory Adjustments | 3,393 | Internal warehouse | N/A |
| Bad Debt Adjustments | 6 | Accounting adjustments | N/A |
| **Total Unique Invoices** | **53,628** | **100% Accounted** | |

---

## 5. Financial Reconciliation

| Revenue Stream | Attributed | Unattributed | Total |
| :--- | :--- | :--- | :--- |
| **Gross Sales** | £17,431,551.16 | £3,091,128.68 | £20,522,679.84 |
| **Cancellations / Refunds** | -£1,087,882.14 | -£377,421.52 | -£1,465,303.66 |
| **Bad Debt Adjustments** | £0.00 | -£147,614.08 | -£147,614.08 |
| **Net Revenue** | **£16,343,669.02** | **£2,566,093.08** | **£18,909,762.10** |

---

## 6. Mathematical Invariants Verification

- **raw_minus_duplicates_equals_retained**: PASSED [✓]
- **transaction_lines_equal_invoice_line_count_sum**: PASSED [✓]
- **transaction_quantities_equal_invoice_quantities**: PASSED [✓]
- **transaction_net_value_equals_invoice_net_value**: PASSED [✓]
- **gross_plus_returns_plus_bad_debt_equals_total_value**: PASSED [✓]
