# RetenSight — Special Stock Code & Service Fee Audit Report

## Executive Summary

- **Audited Stock Codes:** 17
- **Total Transaction Lines Analyzed:** 5,487
- **Total Net Value Analyzed:** £-86,015.13

This audit examines non-standard, service, and administrative stock codes to prevent non-product fees 
or staff adjustments from artificially inflating customer purchase frequency in RFM segmentation.

## Summary Audit Table

| Stock Code | Lines | Total Value (£) | Attributed Value (£) | Unattributed Value (£) | Inferred Nature | Physical Merchandise? | Increments Frequency? |
| :--- | ---: | ---: | ---: | ---: | :--- | :---: | :---: |
| `ADJUST` | 67 | £6,835.24 | £2,038.12 | £4,797.12 | `staff_clerical_adjustment` | No | No |
| `ADJUST2` | 3 | £731.05 | £731.05 | £0.00 | `staff_clerical_adjustment` | No | No |
| `AMAZONFEE` | 36 | £-221,520.50 | £0.00 | £-221,520.50 | `marketplace_platform_fee` | No | No |
| `B` | 6 | £-147,614.08 | £0.00 | £-147,614.08 | `bad_debt_writeoff` | No | No |
| `BANK CHARGES` | 100 | £-35,482.25 | £330.00 | £-35,812.25 | `banking_and_payment_fee` | No | No |
| `CRUK` | 16 | £-7,933.43 | £-7,933.43 | £0.00 | `charity_commission` | No | No |
| `D` | 173 | £-12,879.63 | £-12,785.34 | £-94.29 | `commercial_discount` | No | No |
| `DCGSLBOY` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No |
| `DCGSLGIRL` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No |
| `DCGSSBOY` | 23 | £251.35 | £0.00 | £251.35 | `physical_merchandise` | Yes | Yes |
| `DCGSSGIRL` | 25 | £295.63 | £0.00 | £295.63 | `physical_merchandise` | Yes | Yes |
| `DOT` | 1,425 | £309,844.10 | £11,906.36 | £297,937.74 | `website_delivery_fee` | No | No |
| `GIFT` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No |
| `M` | 1,403 | £-82,935.57 | £-185,325.48 | £102,389.91 | `manual_commercial_adjustment` | No | No |
| `PADS` | 19 | £-36.60 | £-36.60 | £0.00 | `physical_merchandise` | Yes | Yes |
| `POST` | 2,086 | £110,430.41 | £110,338.51 | £91.90 | `postage_and_shipping` | No | No |
| `S` | 102 | £-6,000.85 | £0.00 | £-6,000.85 | `product_sample_writeoff` | No | No |

## Detailed Stock Code Breakdown & Classification Rules

### Stock Code: `ADJUST`
- **Inferred Category:** `staff_clerical_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 67 lines (Customer Attributed: 61, Unattributed: 6)
- **Net Financial Value:** £6,835.24 (Customer Attributed: £2,038.12, Unattributed: £4,797.12)
- **Representative Invoices:** 495732, 495733, 495735
- **Frequent Descriptions:** 'Adjustment by john on 26/01/2010 16' (38), 'Adjustment by john on 26/01/2010 17' (26), 'Adjustment by Peter on 24/05/2010 1' (3)
- **Observed Evidence:** Descriptions specify internal staff adjustments (e.g., 'Adjustment by john on 26/01/2010'). Represents internal ledger reconciliation rather than genuine customer ordering.
- **Applied Treatment Rule:** Classified as special commercial charge or administrative correction. Adjusts monetary value; does not increment purchase frequency.

### Stock Code: `ADJUST2`
- **Inferred Category:** `staff_clerical_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 3 lines (Customer Attributed: 3, Unattributed: 0)
- **Net Financial Value:** £731.05 (Customer Attributed: £731.05, Unattributed: £0.00)
- **Representative Invoices:** 513564, 513566, 513565
- **Frequent Descriptions:** 'Adjustment by Peter on Jun 25 2010' (3)
- **Observed Evidence:** Descriptions specify internal staff corrections ('Adjustment by Peter on Jun 25 2010'). Internal book balance correction.
- **Applied Treatment Rule:** Classified as special commercial charge. Adjusts monetary value; does not increment purchase frequency.

### Stock Code: `AMAZONFEE`
- **Inferred Category:** `marketplace_platform_fee`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 36 lines (Customer Attributed: 0, Unattributed: 36)
- **Net Financial Value:** £-221,520.50 (Customer Attributed: £0.00, Unattributed: £-221,520.50)
- **Representative Invoices:** C531400, 531411, C537600
- **Frequent Descriptions:** 'AMAZON FEE' (36)
- **Observed Evidence:** Description is 'AMAZON FEE'. Deductions taken by Amazon marketplace platform for third-party seller fees.
- **Applied Treatment Rule:** Classified as marketplace fee. Unattributed to customers. Does not affect customer-level RFM.

### Stock Code: `B`
- **Inferred Category:** `bad_debt_writeoff`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 6 lines (Customer Attributed: 0, Unattributed: 6)
- **Net Financial Value:** £-147,614.08 (Customer Attributed: £0.00, Unattributed: £-147,614.08)
- **Representative Invoices:** A506401, A516228, A528059
- **Frequent Descriptions:** 'Adjust bad debt' (6)
- **Observed Evidence:** Description is 'Adjust bad debt'. Invoices are prefixed with 'A' (e.g. A506401). Accounting write-offs of uncollectible balances (£147,614.08).
- **Applied Treatment Rule:** Classified as bad_debt_adjustment. Separated completely from commercial revenue. Never increments customer purchase frequency or counts as positive sales.

### Stock Code: `BANK CHARGES`
- **Inferred Category:** `banking_and_payment_fee`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 100 lines (Customer Attributed: 37, Unattributed: 63)
- **Net Financial Value:** £-35,482.25 (Customer Attributed: £330.00, Unattributed: £-35,812.25)
- **Representative Invoices:** C490943, 490948, C492206
- **Frequent Descriptions:** 'Bank Charges' (100)
- **Observed Evidence:** Description is 'Bank Charges'. Wire fees, international payment processing charges, and merchant costs.
- **Applied Treatment Rule:** Classified as special commercial charge or administrative cost. Does not represent merchandise. Excluded from product repeat purchase frequency.

### Stock Code: `CRUK`
- **Inferred Category:** `charity_commission`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 16 lines (Customer Attributed: 16, Unattributed: 0)
- **Net Financial Value:** £-7,933.43 (Customer Attributed: £-7,933.43, Unattributed: £0.00)
- **Representative Invoices:** C564763, C565382, C566216
- **Frequent Descriptions:** 'CRUK Commission' (16)
- **Observed Evidence:** Description is 'CRUK Commission'. All 16 transactions belong to Customer ID 14096 (Cancer Research UK) as commission payouts or fundraising disbursements.
- **Applied Treatment Rule:** Classified as administrative cancellation/settlement. Excluded from customer purchase frequency.

### Stock Code: `D`
- **Inferred Category:** `commercial_discount`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 173 lines (Customer Attributed: 170, Unattributed: 3)
- **Net Financial Value:** £-12,879.63 (Customer Attributed: £-12,785.34, Unattributed: £-94.29)
- **Representative Invoices:** C489535, C491428, C491845
- **Frequent Descriptions:** 'Discount' (173)
- **Observed Evidence:** Description is 'Discount'. Commercial concessions and rebates granted to trade accounts. All transactions are price reductions.
- **Applied Treatment Rule:** Classified as cancellation/discount credit or special charge. Decreases customer monetary net value. Does not increment purchase frequency.

### Stock Code: `DCGSLBOY`
- **Inferred Category:** `inventory_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
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
- **Transaction Volume:** 1,425 lines (Customer Attributed: 16, Unattributed: 1,409)
- **Net Financial Value:** £309,844.10 (Customer Attributed: £11,906.36, Unattributed: £297,937.74)
- **Representative Invoices:** 489597, 489600, 489601
- **Frequent Descriptions:** 'DOTCOM POSTAGE' (1423), '[BLANK]' (2)
- **Observed Evidence:** Descriptions consist of 'DOTCOM POSTAGE'. Represents batch fulfillment costs for web orders. Almost entirely unattributed to individual retail customer IDs.
- **Applied Treatment Rule:** Classified as special commercial charge. Overwhelmingly unattributed (>98% lines, £297k+). Does not represent physical merchandise and does not increment customer purchase frequency.

### Stock Code: `GIFT`
- **Inferred Category:** `inventory_adjustment`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
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
- **Transaction Volume:** 1,403 lines (Customer Attributed: 1,096, Unattributed: 307)
- **Net Financial Value:** £-82,935.57 (Customer Attributed: £-185,325.48, Unattributed: £102,389.91)
- **Representative Invoices:** 489609, C489651, C489859
- **Frequent Descriptions:** 'Manual' (1403)
- **Observed Evidence:** Description is 'Manual'. Manually keyed administrative corrections, price adjustments, and bespoke wholesale charges without specific merchandise catalog SKU identification.
- **Applied Treatment Rule:** Classified as special commercial charge when positive, cancellation/credit when negative. Adjusts customer monetary net spend. Does not count as a standard catalog merchandise purchase.

### Stock Code: `PADS`
- **Inferred Category:** `physical_merchandise`
- **Physical Merchandise:** Yes
- **Increments Frequency:** Yes (on qualifying invoice)
- **Transaction Volume:** 19 lines (Customer Attributed: 19, Unattributed: 0)
- **Net Financial Value:** £-36.60 (Customer Attributed: £-36.60, Unattributed: £0.00)
- **Representative Invoices:** 494914, 496222, 496473
- **Frequent Descriptions:** 'PADS TO MATCH ALL CUSHIONS' (19)
- **Observed Evidence:** Description is 'PADS TO MATCH ALL CUSHIONS'. Every invoice containing PADS is a multi-line customer order containing 11 to 93 other home decor items.
- **Applied Treatment Rule:** Classified as physical merchandise. Description confirms physical cushion inserts ('PADS TO MATCH ALL CUSHIONS'). When ordered with positive quantity alongside other merchandise, it forms part of valid customer orders. In historical data, 18 lines were priced at nominal £0.001 and 1 cancellation line at -£36.60.

### Stock Code: `POST`
- **Inferred Category:** `postage_and_shipping`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 2,086 lines (Customer Attributed: 1,983, Unattributed: 103)
- **Net Financial Value:** £110,430.41 (Customer Attributed: £110,338.51, Unattributed: £91.90)
- **Representative Invoices:** 489439, 489444, 489447
- **Frequent Descriptions:** 'POSTAGE' (2079), '[BLANK]' (7)
- **Observed Evidence:** Descriptions consist exclusively of 'POSTAGE'. High customer attribution (>95% of lines). Corresponds to standard customer shipping charges incurred during checkout.
- **Applied Treatment Rule:** Classified as special commercial charge. Adjusts customer monetary value (shipping spend). Invoices containing only postage fees (product_sales == 0) do not qualify as product repeat purchases.

### Stock Code: `S`
- **Inferred Category:** `product_sample_writeoff`
- **Physical Merchandise:** No
- **Increments Frequency:** No (Excluded from repeat purchase events)
- **Transaction Volume:** 102 lines (Customer Attributed: 0, Unattributed: 102)
- **Net Financial Value:** £-6,000.85 (Customer Attributed: £0.00, Unattributed: £-6,000.85)
- **Representative Invoices:** C500305, C500309, C502083
- **Frequent Descriptions:** 'SAMPLES' (102)
- **Observed Evidence:** Description is 'SAMPLES'. Internal sample distributions and write-offs. Quantity negative, 0 customer attribution.
- **Applied Treatment Rule:** Classified as sample adjustment. Completely unattributed to customer IDs. Excluded from customer RFM.

## Methodological Conclusions for Customer RFM Pipeline

1. **Postage and Freight (`POST`, `DOT`):** Shipping fees constitute commercial revenue and contribute to total monetary spend, but invoices containing purely postage fees without physical items do not represent product repurchase events.
2. **Manual Adjustments & Discounts (`M`, `D`):** Administrative entries adjust net monetary value (credits/debits), but lack SKU merchandise definitions and must not increment purchase frequency.
3. **Bad Debt & Banking Fees (`B`, `BANK CHARGES`):** Overhead finance items. Bad debt is completely excluded from customer spend. Bank charges adjust finance costs but never increment frequency.
4. **Cushion Pads (`PADS`):** Confirmed as physical merchandise ('PADS TO MATCH ALL CUSHIONS'). When ordered in multi-line purchases alongside cushions, it represents legitimate customer goods.
5. **Staff Adjustments (`ADJUST`, `ADJUST2`):** Clerical internal balance corrections by specific employees. Excluded from customer purchase events.
