# Special Stock Codes and Financial Treatment

Some stock codes in Online Retail II do not represent ordinary catalog products. RetenSight checks these codes separately so that fees and accounting entries do not inflate purchase frequency or distort customer spend.

## Treatment at a glance

| Code | Meaning in this project | Counts as a merchandise purchase? | Included in customer commercial spend? |
|---|---|---:|---:|
| `POST`, `DOT` | Postage and delivery fees | No, not by themselves | Yes |
| `M` | Manual commercial charge or adjustment | No, not by itself | Yes |
| `D` | Commercial discount | No | Yes, as a reduction where negative |
| `PADS` | Cushion pad product | Yes, when the invoice otherwise qualifies | Yes |
| `DCGSSBOY`, `DCGSSGIRL` | Party-bag products | Yes, when the invoice otherwise qualifies | Yes |
| `CRUK` | Charity commission settlement | No | No; tracked as an administrative settlement |
| `BANK CHARGES`, `ADJUST`, `ADJUST2` | Bank or clerical adjustments | No | No; tracked separately |
| `B` | Bad-debt adjustment | No | No; company-level accounting only |
| `AMAZONFEE`, `S` | Marketplace fee or sample write-off | No | No customer spend attribution in this dataset |
| `GIFT`, `DCGSLBOY`, `DCGSLGIRL` | Zero-price inventory entries | No | No |

A commercial charge can affect the amount a customer spent without counting as a product purchase. Purchase frequency only increases for a qualifying merchandise invoice.

## Why the distinction matters

- Shipping fees are commercial spend, but a shipping-only invoice does not establish a repeat merchandise purchase.
- Discounts and manual commercial adjustments affect net commercial spend, but do not increase purchase frequency.
- Administrative settlements are kept for accounting reconciliation, but are excluded from the customer commercial spend used by RFM.
- Bad-debt adjustments stay in company-level financial reporting because they are not customer purchases.
- The `PADS` code was checked as a physical product rather than treated as a fee.

## Financial totals

From the supplied workbook:

| Measure | Total |
|---|---:|
| Gross product sales | £19,716,362.61 |
| Special commercial charges | £806,317.23 |
| Gross commercial sales | £20,522,679.84 |
| Cancellations and returns | -£1,465,303.66 |
| Company-wide net commercial value before bad debt | £19,057,376.18 |
| Bad-debt adjustments | -£147,614.08 |
| Company-wide net invoice value after bad debt | £18,909,762.10 |
| Customer commercial net spend | £16,348,503.28 |
| Customer accounting ledger balance | £16,343,669.02 |

These totals use different scopes. Company-wide values include unattributed transactions; customer commercial spend excludes administrative settlements and bad debt. Do not label them interchangeably.

The full stock-code breakdown and machine-readable audit are in [special_stock_codes_audit.md](../reports/special_stock_codes_audit.md), [special_stock_codes_audit.json](../reports/special_stock_codes_audit.json) and the [data quality audit](../reports/data_quality_audit.json).
