# RetenSight — Special Stock Code & Service Fee Audit Report

## Executive Summary

- **Audited Stock Codes:** 17
- **Total Transaction Lines Analyzed:** 5,487
- **Total Net Value Analyzed:** £-86,015.13

This audit examines non-standard, service, and administrative stock codes to prevent non-product fees 
or staff adjustments from artificially inflating customer purchase frequency or distorting customer commercial spend.

## Summary Audit Table

| Stock Code | Lines | Total Value (£) | Attributed Value (£) | Unattributed Value (£) | Inferred Nature | Physical Merchandise? | Increments Frequency? | Affects Customer Commercial Spend? |
| :--- | ---: | ---: | ---: | ---: | :--- | :---: | :---: | :---: |
| `ADJUST` | 67 | £6,835.24 | £2,038.12 | £4,797.12 | `staff_clerical_adjustment` | No | No | No (Admin / Accounting only) |
| `ADJUST2` | 3 | £731.05 | £731.05 | £0.00 | `staff_clerical_adjustment` | No | No | No (Admin / Accounting only) |
| `AMAZONFEE` | 36 | £-221,520.50 | £0.00 | £-221,520.50 | `marketplace_platform_fee` | No | No | No (Admin / Accounting only) |
| `B` | 6 | £-147,614.08 | £0.00 | £-147,614.08 | `bad_debt_writeoff` | No | No | No (Admin / Accounting only) |
| `BANK CHARGES` | 100 | £-35,482.25 | £330.00 | £-35,812.25 | `banking_and_payment_fee` | No | No | No (Admin / Accounting only) |
| `CRUK` | 16 | £-7,933.43 | £-7,933.43 | £0.00 | `charity_commission` | No | No | No (Admin / Accounting only) |
| `D` | 173 | £-12,879.63 | £-12,785.34 | £-94.29 | `commercial_discount` | No | No | Yes |
| `DCGSLBOY` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | No (Admin / Accounting only) |
| `DCGSLGIRL` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | No (Admin / Accounting only) |
| `DCGSSBOY` | 23 | £251.35 | £0.00 | £251.35 | `physical_merchandise` | Yes | Yes | Yes |
| `DCGSSGIRL` | 25 | £295.63 | £0.00 | £295.63 | `physical_merchandise` | Yes | Yes | Yes |
| `DOT` | 1,425 | £309,844.10 | £11,906.36 | £297,937.74 | `website_delivery_fee` | No | No | Yes |
| `GIFT` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | No (Admin / Accounting only) |
| `M` | 1,403 | £-82,935.57 | £-185,325.48 | £102,389.91 | `manual_commercial_adjustment` | No | No | Yes |
| `PADS` | 19 | £-36.60 | £-36.60 | £0.00 | `physical_merchandise` | Yes | Yes | Yes |
| `POST` | 2,086 | £110,430.41 | £110,338.51 | £91.90 | `postage_and_shipping` | No | No | Yes |
| `S` | 102 | £-6,000.85 | £0.00 | £-6,000.85 | `product_sample_writeoff` | No | No | No (Admin / Accounting only) |

## Detailed Stock Code Breakdown & Classification Rules

### Stock Code: `ADJUST`
- **Inferred Category:** `staff_clerical_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 67 lines (Customer Attributed: 61, Unattributed: 6)
- **Net Financial Value:** £6,835.24 (Customer Attributed: £2,038.12, Unattributed: £4,797.12)
- **Representative Invoices:** 495732, 495733, 495735
- **Frequent Descriptions:** 'Adjustment by john on 26/01/2010 16' (38), 'Adjustment by john on 26/01/2010 17' (26), 'Adjustment by Peter on 24/05/2010 1' (3)
- **Observed Evidence:** Descriptions specify internal staff adjustments (e.g., 'Adjustment by john on 26/01/2010'). Internal book balance corrections by warehouse/accounting personnel.
- **Applied Treatment Rule:** Classified as internal staff clerical adjustment. Excluded from customer commercial spend (isolated under administrative settlements, +£2,038.12 net customer total). Preserved in business-level financial audit.

### Stock Code: `ADJUST2`
- **Inferred Category:** `staff_clerical_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 3 lines (Customer Attributed: 3, Unattributed: 0)
- **Net Financial Value:** £731.05 (Customer Attributed: £731.05, Unattributed: £0.00)
- **Representative Invoices:** 513564, 513566, 513565
- **Frequent Descriptions:** 'Adjustment by Peter on Jun 25 2010' (3)
- **Observed Evidence:** Descriptions specify internal staff corrections ('Adjustment by Peter on Jun 25 2010'). Internal book balance correction.
- **Applied Treatment Rule:** Classified as internal staff clerical adjustment. Excluded from customer commercial spend (isolated under administrative settlements, +£731.05 customer total). Preserved in business-level financial audit.

### Stock Code: `AMAZONFEE`
- **Inferred Category:** `marketplace_platform_fee`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 36 lines (Customer Attributed: 0, Unattributed: 36)
- **Net Financial Value:** £-221,520.50 (Customer Attributed: £0.00, Unattributed: £-221,520.50)
- **Representative Invoices:** C531400, 531411, C537600
- **Frequent Descriptions:** 'AMAZON FEE' (36)
- **Observed Evidence:** Description is 'AMAZON FEE'. Deductions taken by Amazon marketplace platform for third-party seller fees.
- **Applied Treatment Rule:** Classified as marketplace platform fee. 100% unattributed. Excluded from customer RFM; retained in company-level financial audit.

### Stock Code: `B`
- **Inferred Category:** `bad_debt_writeoff`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 6 lines (Customer Attributed: 0, Unattributed: 6)
- **Net Financial Value:** £-147,614.08 (Customer Attributed: £0.00, Unattributed: £-147,614.08)
- **Representative Invoices:** A506401, A516228, A528059
- **Frequent Descriptions:** 'Adjust bad debt' (6)
- **Observed Evidence:** Description is 'Adjust bad debt'. Invoices are prefixed with 'A' (e.g. A506401). 0 customer attribution.
- **Applied Treatment Rule:** Classified as bad_debt_adjustment. Separated completely from customer commercial revenue. Company-level accounting write-off of uncollectible balances (-£147,614.08). Excluded from customer RFM.

### Stock Code: `BANK CHARGES`
- **Inferred Category:** `banking_and_payment_fee`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 100 lines (Customer Attributed: 37, Unattributed: 63)
- **Net Financial Value:** £-35,482.25 (Customer Attributed: £330.00, Unattributed: £-35,812.25)
- **Representative Invoices:** C490943, 490948, C492206
- **Frequent Descriptions:** 'Bank Charges' (100)
- **Observed Evidence:** Description is 'Bank Charges'. Wire transfer fees, international payment processing charges, and merchant operational overhead.
- **Applied Treatment Rule:** Classified as administrative financial fee. Excluded from customer commercial spend (isolated under administrative settlements, +£330.00 customer total). Preserved in business-level financial audit. Excluded from repeat purchase frequency.

### Stock Code: `CRUK`
- **Inferred Category:** `charity_commission`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 16 lines (Customer Attributed: 16, Unattributed: 0)
- **Net Financial Value:** £-7,933.43 (Customer Attributed: £-7,933.43, Unattributed: £0.00)
- **Representative Invoices:** C564763, C565382, C566216
- **Frequent Descriptions:** 'CRUK Commission' (16)
- **Observed Evidence:** Description is 'CRUK Commission'. Payouts / commission disbursements to charity partner Customer 14096, not merchandise purchases or customer returns.
- **Applied Treatment Rule:** Classified as administrative charity commission payout. Excluded from customer commercial spend (isolated under administrative settlements, -£7,933.43). All 16 transactions belong to Customer ID 14096 (Cancer Research UK). Preserved in business-level financial audit.

### Stock Code: `D`
- **Inferred Category:** `commercial_discount`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 173 lines (Customer Attributed: 170, Unattributed: 3)
- **Net Financial Value:** £-12,879.63 (Customer Attributed: £-12,785.34, Unattributed: £-94.29)
- **Representative Invoices:** C489535, C491428, C491845
- **Frequent Descriptions:** 'Discount' (173)
- **Observed Evidence:** Description is 'Discount'. Commercial concessions and rebates granted to trade accounts. Transactions reduce customer account balance.
- **Applied Treatment Rule:** Classified as commercial discount. Reduces customer commercial net spend. Does not increment purchase frequency.

### Stock Code: `DCGSLBOY`
- **Inferred Category:** `inventory_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 1 lines (Customer Attributed: 0, Unattributed: 1)
- **Net Financial Value:** £0.00 (Customer Attributed: £0.00, Unattributed: £0.00)
- **Representative Invoices:** 497811
- **Frequent Descriptions:** '[BLANK]' (1)
- **Observed Evidence:** Zero price inventory entry without customer attribution.
- **Applied Treatment Rule:** Classified as inventory adjustment. Price is £0.00. Excluded from customer RFM.

### Stock Code: `DCGSLGIRL`
- **Inferred Category:** `inventory_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 1 lines (Customer Attributed: 0, Unattributed: 1)
- **Net Financial Value:** £0.00 (Customer Attributed: £0.00, Unattributed: £0.00)
- **Representative Invoices:** 499042
- **Frequent Descriptions:** '[BLANK]' (1)
- **Observed Evidence:** Zero price inventory entry without customer attribution.
- **Applied Treatment Rule:** Classified as inventory adjustment. Price is £0.00. Excluded from customer RFM.

### Stock Code: `DCGSSBOY`
- **Inferred Category:** `physical_merchandise`
- **Physical Merchandise:** Yes
- **Increments Frequency:** Yes (on qualifying invoice)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 23 lines (Customer Attributed: 0, Unattributed: 23)
- **Net Financial Value:** £251.35 (Customer Attributed: £0.00, Unattributed: £251.35)
- **Representative Invoices:** 499040, 512737, 513099
- **Frequent Descriptions:** 'BOYS PARTY BAG' (21), '[BLANK]' (1), 'update' (1)
- **Observed Evidence:** Description is 'BOYS PARTY BAG'. Tangible party goods sold at standard retail unit prices.
- **Applied Treatment Rule:** Classified as standard product merchandise. Walk-in / unattributed sales of boys party bags.

### Stock Code: `DCGSSGIRL`
- **Inferred Category:** `physical_merchandise`
- **Physical Merchandise:** Yes
- **Increments Frequency:** Yes (on qualifying invoice)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 25 lines (Customer Attributed: 0, Unattributed: 25)
- **Net Financial Value:** £295.63 (Customer Attributed: £0.00, Unattributed: £295.63)
- **Representative Invoices:** 496722, 512738, 513099
- **Frequent Descriptions:** 'GIRLS PARTY BAG' (23), '[BLANK]' (1), 'update' (1)
- **Observed Evidence:** Description is 'GIRLS PARTY BAG'. Tangible party goods sold at standard retail unit prices.
- **Applied Treatment Rule:** Classified as standard product merchandise. Walk-in / unattributed sales of girls party bags.

### Stock Code: `DOT`
- **Inferred Category:** `website_delivery_fee`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 1,425 lines (Customer Attributed: 16, Unattributed: 1,409)
- **Net Financial Value:** £309,844.10 (Customer Attributed: £11,906.36, Unattributed: £297,937.74)
- **Representative Invoices:** 489597, 489600, 489601
- **Frequent Descriptions:** 'DOTCOM POSTAGE' (1423), '[BLANK]' (2)
- **Observed Evidence:** Descriptions consist of 'DOTCOM POSTAGE'. Batch fulfillment delivery fees for web orders. Overwhelmingly unattributed; customer-attributed lines belong to corporate partner account 14096.
- **Applied Treatment Rule:** Classified as special commercial charge. Customer-attributed portion (16 lines, £11,906.36 on Customer 14096) represents delivery fees and affects commercial spend. Unattributed portion (£297,937.74) remains in whole-company financial reconciliation. Does not increment purchase frequency.

### Stock Code: `GIFT`
- **Inferred Category:** `inventory_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 1 lines (Customer Attributed: 0, Unattributed: 1)
- **Net Financial Value:** £0.00 (Customer Attributed: £0.00, Unattributed: £0.00)
- **Representative Invoices:** 497107
- **Frequent Descriptions:** '[BLANK]' (1)
- **Observed Evidence:** Zero price administrative inventory movement without customer transaction value.
- **Applied Treatment Rule:** Classified as inventory adjustment. Price is £0.00, customer ID is missing. Excluded from customer RFM.

### Stock Code: `M`
- **Inferred Category:** `manual_commercial_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 1,403 lines (Customer Attributed: 1,096, Unattributed: 307)
- **Net Financial Value:** £-82,935.57 (Customer Attributed: £-185,325.48, Unattributed: £102,389.91)
- **Representative Invoices:** 489609, C489651, C489859
- **Frequent Descriptions:** 'Manual' (1403)
- **Observed Evidence:** Description is 'Manual'. Manually keyed administrative corrections, price adjustments, and bespoke wholesale charges without specific merchandise catalog SKU identification.
- **Applied Treatment Rule:** Classified as special commercial charge when positive, cancellation/credit when negative. Adjusts customer commercial net spend (custom bespoke billing / concession). Does not count as a standard catalog merchandise repeat purchase.

### Stock Code: `PADS`
- **Inferred Category:** `physical_merchandise`
- **Physical Merchandise:** Yes
- **Increments Frequency:** Yes (on qualifying invoice)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 19 lines (Customer Attributed: 19, Unattributed: 0)
- **Net Financial Value:** £-36.60 (Customer Attributed: £-36.60, Unattributed: £0.00)
- **Representative Invoices:** 494914, 496222, 496473
- **Frequent Descriptions:** 'PADS TO MATCH ALL CUSHIONS' (19)
- **Observed Evidence:** Description is 'PADS TO MATCH ALL CUSHIONS'. Every invoice containing PADS is a multi-line customer order containing 11 to 93 other home decor items.
- **Applied Treatment Rule:** Classified as standard catalog physical merchandise. Description confirms physical cushion inserts ('PADS TO MATCH ALL CUSHIONS'). Ordered alongside cushion covers in multi-line customer orders. Positive lines are classified as standard_product_sale; returns as standard merchandise returns.

### Stock Code: `POST`
- **Inferred Category:** `postage_and_shipping`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** Yes (Included in net commercial spend)
- **Transaction Volume:** 2,086 lines (Customer Attributed: 1,983, Unattributed: 103)
- **Net Financial Value:** £110,430.41 (Customer Attributed: £110,338.51, Unattributed: £91.90)
- **Representative Invoices:** 489439, 489444, 489447
- **Frequent Descriptions:** 'POSTAGE' (2079), '[BLANK]' (7)
- **Observed Evidence:** Descriptions consist exclusively of 'POSTAGE'. High customer attribution (>95% of lines). Corresponds to standard customer shipping charges incurred during checkout.
- **Applied Treatment Rule:** Classified as special commercial charge. Shipping costs paid by customers affect customer commercial spend. Invoices containing only shipping fees (product_sales == 0) do not qualify as product repeat purchases.

### Stock Code: `S`
- **Inferred Category:** `product_sample_writeoff`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Affects Customer Commercial Spend:** No (Isolated under administrative settlements)
- **Transaction Volume:** 102 lines (Customer Attributed: 0, Unattributed: 102)
- **Net Financial Value:** £-6,000.85 (Customer Attributed: £0.00, Unattributed: £-6,000.85)
- **Representative Invoices:** C500305, C500309, C502083
- **Frequent Descriptions:** 'SAMPLES' (102)
- **Observed Evidence:** Description is 'SAMPLES'. Internal sample distributions and write-offs. Quantity negative, 0 customer attribution.
- **Applied Treatment Rule:** Classified as sample adjustment. Completely unattributed. Excluded from customer RFM.

## Methodological Conclusions for Customer RFM Pipeline

1. **Postage and Freight (`POST`, `DOT`):** Shipping fees constitute commercial revenue and contribute to customer commercial spend, but invoices containing purely postage fees without physical items do not represent product repeat purchases.
2. **Manual Adjustments & Discounts (`M`, `D`):** Commercial entries adjust customer net commercial spend (credits/debits), but lack catalog SKU merchandise definitions and do not increment purchase frequency.
3. **Administrative Settlements (`CRUK`, `ADJUST`, `ADJUST2`, `BANK CHARGES`):** Clerical balance adjustments, bank processing fees, and charity commission payouts are isolated from customer commercial spend. They are preserved in whole-company financial reconciliation and tracked separately under `monetary_admin_settlements`.
4. **Cushion Pads (`PADS`):** Confirmed as physical catalog merchandise ('PADS TO MATCH ALL CUSHIONS'). Reclassified as `standard_product_sale` (or merchandise return if cancelled).
5. **Overhead / Unattributed Items (`B`, `AMAZONFEE`, `S`):** Bad debt adjustments, platform seller fees, and non-commercial sample distributions have 0 customer attribution and remain strictly in business accounting auditing.
