# Data Cleaning Rules

This guide explains how RetenSight turns the source workbook into reliable transaction and customer tables.

## Source data

The UCI Online Retail II workbook contains two sheets:

- `Year 2009-2010`
- `Year 2010-2011`

Together they contain **1,067,371 rows**. The sheets overlap from 1 December to 9 December 2010, so some rows appear in both.

## Cleaning steps

1. **Check the workbook.** Confirm that both sheets and the expected columns are present. Normalize names and data types, and keep the source sheet and row number for traceability.
2. **Remove only verified cross-sheet copies.** Match all eight original fields and preserve the number of repeated occurrences. Remove a confirmed duplicate from the second sheet only. Do not deduplicate rows within one sheet.
3. **Calculate line value.** Use `quantity × price` and retain signs so sales, returns and adjustments can be reconciled.
4. **Classify each line.** Mark merchandise sales, commercial fees, cancellations, bad-debt adjustments, inventory movements and promotional freebies separately.
5. **Build invoice and customer tables.** Aggregate invoice lines before creating customer-level features. This avoids counting one multi-line invoice as multiple purchases.
6. **Check totals.** Compare row counts, quantities and financial components across the cleaned lines, invoices and customer accounts.

## Key rules

| Record type | Treatment |
|---|---|
| Verified copy across workbook sheets | Remove the extra copy from sheet two |
| Repeated line within the same sheet | Preserve it |
| Invoice beginning with `C` | Classify as cancellation/return; do not count as a purchase event |
| Invoice beginning with `A` / code `B` | Track as bad debt at company level; exclude from customer spend |
| Postage or delivery fee (`POST`, `DOT`) | Include in commercial spend, but do not count as a merchandise purchase by itself |
| Manual commercial adjustment (`M`) or discount (`D`) | Include in commercial spend; do not increase purchase frequency |
| Administrative settlement (`CRUK`, `BANK CHARGES`, `ADJUST`, `ADJUST2`) | Keep in the accounting audit, separate from customer commercial spend |
| Zero-price customer gift | Retain in the cleaned data, but exclude from the commercial modelling extract |
| Zero-price unattributed inventory movement | Keep in the audit; exclude from customer analysis |

The code treats the `PADS` stock code as physical merchandise. It also flags an unusual positive line on a cancellation invoice instead of silently changing its value.

## Results from the supplied workbook

| Check | Result |
|---|---:|
| Rows ingested | 1,067,371 |
| Verified cross-sheet duplicates removed | 22,523 |
| Rows retained | 1,044,848 |
| Customer-attributed rows | 809,561 |
| Customer commercial-ready rows | 809,491 |
| Customer commercial-ready records excluded as zero-price gifts | 70 |
| Unique invoices | 53,628 |
| Customers with a qualifying purchase history | 5,942 |

Company-wide net invoice value after bad-debt adjustments is **£18,909,762.10**. Customer commercial net spend totals **£16,348,503.28**; the figures differ because unattributed transactions, bad debt and administrative settlements are treated separately. See the generated [reconciliation report](../reports/cleaning_and_reconciliation_summary.md).

## Run it

Place the workbook at `data/raw/online_retail_II.xlsx`, install requirements, then run:

```bash
python -m retensight.pipeline
```

The pipeline writes the cleaned tables and audit reports to the configured output and reports folders.
