# Special Stock-Code Audit

RetenSight reviewed **17 stock codes** across **5,487 transaction lines**. The audit separates physical products, commercial fees and administrative entries so they do not distort purchase frequency or customer spend. The combined audited value is **-£86,015.13**.

## Audited codes

| Code | Lines | Total value (£) | Category | Merchandise? | Counts as purchase? | Included in customer commercial spend? |
|---|---:|---:|---|:---:|:---:|:---:|
| POST | 2,086 | 110,430.41 | postage_and_shipping | No | No | Yes |
| DOT | 1,425 | 309,844.10 | website_delivery_fee | No | No | Yes |
| M | 1,403 | -82,935.57 | manual_commercial_adjustment | No | No | Yes |
| D | 173 | -12,879.63 | commercial_discount | No | No | Yes |
| BANK CHARGES | 100 | -35,482.25 | banking_and_payment_fee | No | No | No |
| CRUK | 16 | -7,933.43 | charity_commission | No | No | No |
| ADJUST | 67 | 6,835.24 | staff_clerical_adjustment | No | No | No |
| ADJUST2 | 3 | 731.05 | staff_clerical_adjustment | No | No | No |
| B | 6 | -147,614.08 | bad_debt_writeoff | No | No | No |
| AMAZONFEE | 36 | -221,520.50 | marketplace_platform_fee | No | No | No |
| S | 102 | -6,000.85 | product_sample_writeoff | No | No | No |
| PADS | 19 | -36.60 | physical_merchandise | Yes | Yes | Yes |
| DCGSSBOY | 23 | 251.35 | physical_merchandise | Yes | Yes | Yes |
| DCGSSGIRL | 25 | 295.63 | physical_merchandise | Yes | Yes | Yes |
| GIFT | 1 | 0.00 | inventory_adjustment | No | No | No |
| DCGSLBOY | 1 | 0.00 | inventory_adjustment | No | No | No |
| DCGSLGIRL | 1 | 0.00 | inventory_adjustment | No | No | No |

## Rules that matter for CRM

- POST and DOT are commercial shipping fees. They affect spend but do not count as merchandise purchases on their own.
- M and D adjust commercial spend but do not increase purchase frequency.
- CRUK, BANK CHARGES, ADJUST and ADJUST2 are administrative settlements. They are reported separately from customer commercial spend.
- B records bad debt and stays in company-level accounting.
- PADS, DCGSSBOY and DCGSSGIRL are treated as physical merchandise.
- Unattributed fees such as AMAZONFEE and sample write-offs remain in the company audit but are not assigned to customer RFM profiles.

The companion [JSON audit](special_stock_codes_audit.json) retains detailed evidence, descriptions and sample invoices for each code.
