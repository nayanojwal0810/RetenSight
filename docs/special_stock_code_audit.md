# RetenSight — Special Stock Code & Commercial Fee Audit Documentation

## 1. Context and Problem Statement

In retail transaction pipelines, non-merchandise line items frequently appear alongside standard catalog products. If administrative stock codes, delivery surcharges, banking fees, or staff clerical adjustments are naively counted as merchandise sales, they distort downstream analytics:
- Customers paying postage or delivery surcharges appear to make multiple "product purchases".
- Internal staff reconciliations or manual corrections inflate repeat purchase counts.
- Zero-revenue sample distributions or bad debt adjustments distort customer spend.
- Administrative partner disbursements or staff clerical entries distort customer commercial spend.

This document establishes an evidence-based taxonomy and audit methodology for all non-standard stock codes identified across the 1,044,848 retained transactions in the UCI Online Retail II dataset, distinguishing between whole-company financial accounting and customer commercial spend.

---

## 2. Complete Stock Code Taxonomy & Empirical Audit

The table below summarizes all audited special, alpha, and non-numeric stock codes identified in the dataset:

| Stock Code | Lines | Total Value (£) | Attributed Value (£) | Unattributed Value (£) | Inferred Nature | Physical Merchandise? | Increments Frequency? | Affects Commercial Spend? | Treatment Rule & Impact |
| :--- | ---: | ---: | ---: | ---: | :--- | :---: | :---: | :---: | :--- |
| `POST` | 2,086 | £110,430.41 | £110,338.51 | £91.90 | `postage_and_shipping` | No | No | **Yes** | Standard customer shipping fee. Affects customer commercial spend. Invoices with only shipping do not qualify as repeat purchases. |
| `DOT` | 1,425 | £309,844.10 | £11,906.36 | £297,937.74 | `website_delivery_fee` | No | No | **Yes** | E-commerce web delivery fee. Customer portion (£11,906.36) affects commercial spend; unattributed remains in company audit. |
| `M` | 1,403 | -£82,935.57 | -£185,325.48 | £102,389.91 | `manual_adjustment` | No | No | **Yes** | Manually keyed commercial entry / adjustment. Adjusts customer commercial net spend; does not increment repeat product purchases. |
| `D` | 173 | -£12,879.63 | -£12,785.34 | -£94.29 | `commercial_discount` | No | No | **Yes** | Commercial trade discount concession. Adjusts customer commercial net spend (credit). |
| `BANK CHARGES` | 100 | -£35,482.25 | £330.00 | -£35,812.25 | `banking_fee` | No | No | **No** | Merchant banking and wire fee. Excluded from customer commercial spend (isolated under administrative settlements). |
| `CRUK` | 16 | -£7,933.43 | -£7,933.43 | £0.00 | `charity_commission` | No | No | **No** | Cancer Research UK partnership commission payout (Customer 14096). Excluded from customer commercial spend. |
| `ADJUST` | 67 | £6,835.24 | £2,038.12 | £4,797.12 | `clerical_adjustment` | No | No | **No** | Internal staff balance correction (e.g. 'Adjustment by john'). Excluded from customer commercial spend. |
| `ADJUST2` | 3 | £731.05 | £731.05 | £0.00 | `clerical_adjustment` | No | No | **No** | Internal staff clerical adjustment ('Adjustment by Peter'). Excluded from customer commercial spend. |
| `B` | 6 | -£147,614.08 | £0.00 | -£147,614.08 | `bad_debt_writeoff` | No | No | **No** | Accounting bad debt adjustment (Invoices prefixed 'A'). Completely excluded from customer spend. |
| `AMAZONFEE` | 36 | -£221,520.50 | £0.00 | -£221,520.50 | `marketplace_fee` | No | No | **No** | Amazon seller platform fees. 100% unattributed. Excluded from customer RFM. |
| `S` | 102 | -£6,000.85 | £0.00 | -£6,000.85 | `sample_writeoff` | No | No | **No** | Non-commercial product sample distribution. 100% unattributed. Excluded from customer RFM. |
| `PADS` | 19 | -£36.60 | -£36.60 | £0.00 | `physical_merchandise` | **Yes** | **Yes** | **Yes** | Confirmed physical merchandise ('PADS TO MATCH ALL CUSHIONS'). Ordered alongside cushion lines. |
| `DCGSSBOY` | 23 | £251.35 | £0.00 | £251.35 | `physical_merchandise` | **Yes** | **Yes** | **Yes** | Physical merchandise ('BOYS PARTY BAG'). Walk-in / unattributed sales. |
| `DCGSSGIRL` | 25 | £295.63 | £0.00 | £295.63 | `physical_merchandise` | **Yes** | **Yes** | **Yes** | Physical merchandise ('GIRLS PARTY BAG'). Walk-in / unattributed sales. |
| `GIFT` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | **No** | Administrative zero-price inventory movement. Excluded from customer RFM. |
| `DCGSLBOY` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | **No** | Zero-price inventory entry. Excluded from customer RFM. |
| `DCGSLGIRL` | 1 | £0.00 | £0.00 | £0.00 | `inventory_adjustment` | No | No | **No** | Zero-price inventory entry. Excluded from customer RFM. |

---

## 3. Deep Dive into Audited Stock Codes

### 3.1. Cushion Pads (`PADS`) — Confirmed Merchandise
- **Description:** `"PADS TO MATCH ALL CUSHIONS"`
- **Empirical Analysis:** 19 transaction lines appear in the dataset across 19 unique invoices. In 18 of these invoices, the customer ordered between 11 and 93 other home decor items (cushion covers, fabrics, accessories). Cushion pads represent tangible merchandise (cushion filling inserts). 
- **Pricing:** The unit price on 18 lines was set to £0.001 (totaling £0.00 net), serving as an bundled insert, while invoice `C513477` reflects a single return line of -£36.60.
- **Classification:** Reclassified as **physical merchandise** (`standard_product_sale`).

### 3.2. Administrative Staff Corrections (`ADJUST`, `ADJUST2`)
- **Descriptions:** `"Adjustment by john on 26/01/2010 16"`, `"Adjustment by john on 26/01/2010 17"`, `"Adjustment by Peter on Jun 25 2010"`.
- **Empirical Analysis:** 70 transactions total £7,566.29 (£2,769.17 customer-attributed, £4,797.12 unattributed). Rather than customer-initiated e-commerce orders, these represent internal adjustments made directly in the accounting system by warehouse and billing staff.
- **Classification:** **Clerical administrative adjustments**. They are isolated under administrative settlements and excluded from customer commercial spend and qualifying purchase events. Preserved in company accounting reconciliation.

### 3.3. Manual Commercial Transactions (`M`)
- **Description:** `"Manual"`
- **Empirical Analysis:** 1,403 lines with a net impact of -£82,935.57 (-£185,325.48 customer-attributed, £102,389.91 unattributed).
- **Classification:** **Manual commercial adjustments**. Because they lack catalog SKU product descriptions, they represent custom billing adjustments, freight top-ups, or concessions. They adjust customer commercial net spend, but invoices containing solely `M` do not count as catalog merchandise purchases.

### 3.4. Commercial Discounts (`D`)
- **Description:** `"Discount"`
- **Empirical Analysis:** 173 lines totaling -£12,879.63, of which 170 lines (-£12,785.34) are customer-attributed.
- **Classification:** **Commercial discounts / concessions**. These entries reduce customer commercial spend (negative monetary value) and are excluded from purchase frequency increments.

### 3.5. Cancer Research UK Commission (`CRUK`)
- **Description:** `"CRUK Commission"`
- **Empirical Analysis:** 16 transactions totaling -£7,933.43. All 16 transactions belong to customer ID 14096 (Cancer Research UK).
- **Classification:** **Charity partnership commission / payout**. Administrative partner settlement payout, not retail merchandise ordering. Isolated under administrative settlements and excluded from customer commercial spend.

### 3.6. Bank Charges (`BANK CHARGES`)
- **Description:** `"Bank Charges"`
- **Empirical Analysis:** 100 transactions totaling -£35,482.25 (+£330.00 customer-attributed across 12 lines, -£35,812.25 unattributed).
- **Classification:** **Merchant banking and payment processing fees**. Operational overhead excluded from customer commercial spend.

---

## 4. Multi-Layer Financial Reconciliation

The architecture maintains an unambiguous three-tier reconciliation between accounting and commercial CRM representations:

1. **Company Financial Accounting (All Transactions)**:
   - Standard Product Sales (including PADS): £19,716,362.61
   - Special Commercial Charges: £806,317.23
   - Cancellations & Credit Notes: -£1,465,303.66
   - Bad Debt Adjustments: -£147,614.08
   - **Net Company Accounting Revenue**: **£18,909,762.10** (reconciles exactly to £0.00 discrepancy).
   - *Split*: Attributed Account Balance: £16,343,669.02 | Unattributed Corporate Balance: £2,566,093.08.

2. **Customer Account Ledger (Attributed Transactions)**:
   - Total Account Balance across 5,942 customers: **£16,343,669.02**
   - Customer Administrative Settlements (`CRUK`, `BANK CHARGES`, `ADJUST`, `ADJUST2`): **-£4,834.26**

3. **Customer Commercial Spend (CRM Analytics Baseline)**:
   - Total Customer Commercial Net Spend: **£16,348,503.28**
   - Formula: $\text{net\_commercial\_spend} = \text{total\_account\_balance} - \text{admin\_settlements} = £16,343,669.02 - (-£4,834.26) = £16,348,503.28$.
   - Fully traced by subcomponents:
     $$\text{net\_commercial\_spend} = \text{M}_{\text{merchandise}} + \text{M}_{\text{shipping}} + \text{M}_{\text{discounts}} + \text{M}_{\text{returns}} + \text{M}_{\text{manual\_charges}}$$

---

## 5. Sensitivity Analysis: Admin Settlements Inclusion vs Exclusion

To evaluate the operational risk of excluding administrative settlements from customer commercial spend, a sensitivity audit was executed on the full dataset (5,942 customer accounts) and the 24-month customer population (5,853 qualifying customers on 2011-12-09):

- **Full Dataset Population (5,942 customer IDs)**:
  - **74** customer accounts have at least one administrative settlement transaction.
  - **69** accounts have a non-zero net administrative settlement balance (totaling -£4,834.26).
  - **5** accounts have net zero-sum administrative transactions (debits exactly offset credits).
- **2011-12-09 RFM Snapshot (5,853 qualifying customers)**:
  - **53** qualifying customer accounts have at least one administrative settlement line.
  - **48** qualifying customer accounts have a non-zero net administrative settlement balance.
  - **5** qualifying accounts have net zero-sum administrative balances.
  - **21** customer accounts with administrative transactions had 0 qualifying merchandise purchases across 24 months and are excluded from RFM scoring.
- **Top Impact Account (Customer ID 14096 - Cancer Research UK)**:
  - Commercial Net Spend (Excl. Admin): £57,946.49 ($M=5$)
  - Total Account Balance (Incl. Admin): £50,013.06 ($M=5$)
  - Admin Difference: -£7,933.43 (charity commission payouts).
  - Recency = 4 days ($R=5$), Frequency = 84 orders ($F=5$).
  - **Segment Assignment**: **Champions** under both definitions.
- **Segment Stability**: Across all 5,853 customers, exactly **0 customer segment reassignments** occurred when comparing commercial net spend vs total account balance ($100.0\%$ stability).
- **Conclusion**: Isolating administrative settlements provides clean commercial spend without distorting customer tier or queue prioritization.
