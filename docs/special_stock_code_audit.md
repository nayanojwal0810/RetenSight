# RetenSight — Special Stock Code & Commercial Fee Audit Documentation

## 1. Context and Problem Statement

In retail transaction pipelines, non-merchandise line items frequently appear alongside standard catalog products. If administrative stock codes, delivery surcharges, banking fees, or staff clerical adjustments are naively counted as merchandise sales, they distort downstream analytics:
- Customers paying postage or delivery surcharges appear to make multiple "product purchases".
- Internal staff reconciliations or manual corrections inflate repeat purchase counts.
- Zero-revenue sample distributions or bad debt adjustments distort customer spend.

This document establishes an evidence-based taxonomy and audit methodology for all non-standard stock codes identified across the 1,044,848 retained transactions in the UCI Online Retail II dataset.

---

## 2. Complete Stock Code Taxonomy & Empirical Audit

The table below summarizes all 17 audited special, alpha, and non-numeric stock codes identified in the dataset:

| Stock Code | Lines | Total Value (£) | Attributed Value (£) | Unattributed Value (£) | Inferred Nature | Physical Merchandise? | Increments Frequency? | Treatment Rule & Impact |
| :--- | ---: | ---: | ---: | ---: | :--- | :---: | :---: | :--- |
| `POST` | 2,086 | £110,430.41 | £110,338.51 | £91.90 | `postage_and_shipping` | No | No | Shipping charge. Adjusts customer monetary value. Excluded from qualifying product purchase events. |
| `DOT` | 1,425 | £309,844.10 | £11,906.36 | £297,937.74 | `website_delivery_fee` | No | No | E-commerce web delivery fee. Overwhelmingly unattributed. Excluded from customer purchase frequency. |
| `M` | 1,403 | -£82,935.57 | -£185,325.48 | £102,389.91 | `manual_adjustment` | No | No | Manually keyed commercial entry / adjustment. Adjusts net spend; does not increment repeat product purchases. |
| `D` | 173 | -£12,879.63 | -£12,785.34 | -£94.29 | `commercial_discount` | No | No | Commercial trade discount concession. Adjusts customer monetary net spend (credit). |
| `BANK CHARGES` | 100 | -£35,482.25 | £330.00 | -£35,812.25 | `banking_fee` | No | No | Merchant banking and wire fee. Excluded from product repeat purchase frequency. |
| `CRUK` | 16 | -£7,933.43 | -£7,933.43 | £0.00 | `charity_commission` | No | No | Cancer Research UK partnership commission payout (Customer 14096). Excluded from purchase frequency. |
| `ADJUST` | 67 | £6,835.24 | £2,038.12 | £4,797.12 | `clerical_adjustment` | No | No | Internal staff balance correction (e.g. 'Adjustment by john'). Excluded from repeat purchase events. |
| `ADJUST2` | 3 | £731.05 | £731.05 | £0.00 | `clerical_adjustment` | No | No | Internal staff clerical adjustment ('Adjustment by Peter'). Excluded from customer repeat purchase events. |
| `B` | 6 | -£147,614.08 | £0.00 | -£147,614.08 | `bad_debt_writeoff` | No | No | Accounting bad debt adjustment (Invoices prefixed 'A'). Completely excluded from customer spend. |
| `AMAZONFEE` | 36 | -£221,520.50 | £0.00 | -£221,520.50 | `marketplace_fee` | No | No | Amazon seller platform fees. 100% unattributed. Excluded from customer RFM. |
| `S` | 102 | -£6,000.85 | £0.00 | -£6,000.85 | `sample_writeoff` | No | No | Non-commercial product sample distribution. 100% unattributed. Excluded from customer RFM. |
| `PADS` | 19 | -£36.60 | -£36.60 | £0.00 | `physical_merchandise` | **Yes** | **Yes** | Confirmed physical merchandise ('PADS TO MATCH ALL CUSHIONS'). Ordered alongside cushion lines. |
| `DCGSSBOY` | 23 | £251.35 | £0.00 | £251.35 | `physical_merchandise` | **Yes** | **Yes** | Physical merchandise ('BOYS PARTY BAG'). Walk-in / unattributed sales. |
| `DCGSSGIRL` | 25 | £295.63 | £0.00 | £295.63 | `physical_merchandise` | **Yes** | **Yes** | Physical merchandise ('GIRLS PARTY BAG'). Walk-in / unattributed sales. |
| `GIFT` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | Administrative zero-price inventory movement. Excluded from customer RFM. |
| `DCGSLBOY` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | Zero-price inventory entry. Excluded from customer RFM. |
| `DCGSLGIRL` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | Zero-price inventory entry. Excluded from customer RFM. |

---

## 3. Deep Dive into Specific Questioned Stock Codes

### 3.1. Cushion Pads (`PADS`)
- **Description:** `"PADS TO MATCH ALL CUSHIONS"`
- **Empirical Analysis:** 19 transaction lines appear in the dataset across 19 unique invoices. In 18 of these invoices, the customer ordered between 11 and 93 other home decor items (cushion covers, fabrics, accessories). Cushion pads represent tangible merchandise (cushion filling inserts). 
- **Pricing:** The unit price on 18 lines was set to £0.001 (totaling £0.00 net), serving as an bundled insert, while invoice `C513477` reflects a single return line of -£36.60.
- **Classification:** Reclassified as **physical merchandise**.

### 3.2. Administrative Staff Corrections (`ADJUST`, `ADJUST2`)
- **Descriptions:** `"Adjustment by john on 26/01/2010 16"`, `"Adjustment by john on 26/01/2010 17"`, `"Adjustment by Peter on Jun 25 2010"`.
- **Empirical Analysis:** 70 transactions total £7,566.29. Rather than customer-initiated e-commerce orders, these represent internal adjustments made directly in the accounting system by warehouse and billing staff.
- **Classification:** **Clerical administrative adjustments**. They adjust ledger value but are strictly excluded from qualifying customer purchase events.

### 3.3. Manual Commercial Transactions (`M`)
- **Description:** `"Manual"`
- **Empirical Analysis:** 1,403 lines with a net impact of -£82,935.57 (£-185,325.48 customer-attributed, £102,389.91 unattributed).
- **Classification:** **Manual commercial adjustments**. Because they lack catalog SKU product descriptions, they represent custom billing adjustments, freight top-ups, or concessions. They adjust total customer monetary spend, but invoices containing solely `M` do not count as catalog merchandise purchases.

### 3.4. Commercial Discounts (`D`)
- **Description:** `"Discount"`
- **Empirical Analysis:** 173 lines totaling -£12,879.63, of which 170 lines (£-12,785.34) are customer-attributed.
- **Classification:** **Commercial discounts / concessions**. These entries reduce customer spend (negative monetary value) and are excluded from purchase frequency increments.

### 3.5. Cancer Research UK Commission (`CRUK`)
- **Description:** `"CRUK Commission"`
- **Empirical Analysis:** 16 transactions totaling -£7,933.43. All 16 transactions belong to customer ID 14096 (Cancer Research UK).
- **Classification:** **Charity partnership commission / payout**. Administrative partner settlement, not retail merchandise ordering.

---

## 4. Implementation Rule in the RFM Pipeline

To enforce these audit findings deterministically:
1. `invoice_aggregates` computes `product_sales` strictly from lines classified as `standard_product_sale` (which excludes administrative charges, discounts, and fees).
2. A customer invoice qualifies as a purchase event if and only if:
   $$\text{product\_sales} > 0 \quad \land \quad \text{is\_cancellation} = \text{False} \quad \land \quad \text{is\_bad\_debt} = \text{False} \quad \land \quad \text{total\_quantity} > 0$$
3. Invoices containing only shipping charges (`POST`, `DOT`) or manual entries (`M`, `D`) have $\text{product\_sales} = 0.0$ and **never** increment customer purchase frequency.
