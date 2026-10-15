# RetenSight — Customer RFM Feature Definitions & Segmentation Methodology

## 1. Overview & Objectives

Customer repeat purchase and relationship management (CRM) requires robust, leakage-safe historical feature representations. This document establishes the exact mathematical formulas, data grain aggregations, tie-breaking rules, monetary component tracing, 125-cell monetary-aware segmentation rules, and 90-day evaluation calendar implemented in RetenSight.

---

## 2. Qualifying Purchase Event Definition

To prevent non-product administrative fees (such as shipping surcharges or ledger adjustments) and cancellations from artificially inflating customer purchase frequency, qualifying purchase events are defined strictly at the **invoice grain**:

An invoice $i$ qualifies as a purchase event if and only if all of the following criteria hold:
1. **Valid Customer Attribution:** $\text{customer\_id}_i \text{ is not NULL}$.
2. **Temporal Validity:** $\text{invoice\_date}_i \le T_{\text{snapshot}}$.
3. **Non-Cancellation:** $\text{is\_cancellation}_i = \text{False}$ (invoice number does not start with `'C'`).
4. **Non-Bad-Debt:** $\text{is\_bad\_debt}_i = \text{False}$ (invoice number does not start with `'A'`).
5. **Positive Merchandise Sales:** $\text{product\_sales}_i > 0.0$ (invoice contains at least one positive standard catalog merchandise line).
6. **Positive Net Quantity:** $\text{total\_quantity}_i > 0$.

### Handling Invariants
- **Multi-line Invoices:** Aggregation occurs at the unique invoice ID grain ($\text{nunique}(\text{invoice})$). An invoice containing 50 line items counts as exactly **1** qualifying purchase event, preventing line count from leaking into frequency.
- **Charge-Only Invoices:** Invoices containing solely postage fees (`POST`, `DOT`) or manual fees (`M`) have $\text{product\_sales} = 0.0$ and do not count as purchases.
- **Same-Day Invoices:** For customers who placed multiple orders on the same calendar day (e.g., morning and afternoon orders with distinct invoice IDs), each invoice is tracked as an independent purchase order ($\text{frequency}$). In addition, $\text{distinct\_purchase\_days}$ is recorded to reflect daily purchase cadence without multi-order bias.

---

## 3. Mathematical Feature Formulations

For an eligible customer $c$ with qualifying purchase set $\mathcal{I}_c = \{i \mid \text{qualifying}(i) \land \text{customer}(i) = c \land \text{date}(i) \le T_{\text{snapshot}}\}$:

### 3.1. Recency ($\text{Recency}$)
The whole number of days elapsed between the customer's most recent qualifying purchase and the snapshot cutoff:
$$\text{Recency}_c = \left\lfloor \frac{T_{\text{snapshot}} - \max_{i \in \mathcal{I}_c}(\text{invoice\_date}_i)}{86400 \text{ seconds}} \right\rfloor$$
- Invariant: $\text{Recency}_c \ge 0$.

### 3.2. Customer Tenure ($\text{Tenure}$)
The whole number of days elapsed since the customer's very first qualifying purchase:
$$\text{Tenure}_c = \left\lfloor \frac{T_{\text{snapshot}} - \min_{i \in \mathcal{I}_c}(\text{invoice\_date}_i)}{86400 \text{ seconds}} \right\rfloor$$
- Invariant: $\text{Tenure}_c \ge \text{Recency}_c$.

### 3.3. Frequency ($\text{Frequency}$)
The total count of distinct qualifying purchase invoices up to the cutoff:
$$\text{Frequency}_c = |\mathcal{I}_c| = \text{count of distinct qualifying purchase invoices}$$

### 3.4. Distinct Purchase Days
The count of unique calendar dates on which the customer completed at least one qualifying purchase:
$$\text{DistinctDays}_c = \text{nunique}(\text{date}(\text{invoice\_date}_i)) \quad \text{for } i \in \mathcal{I}_c$$
- Invariant: $1 \le \text{DistinctDays}_c \le \text{Frequency}_c$.

### 3.5. Component-Level Monetary Values
Calculated across all historical customer invoices $\mathcal{J}_c$ on or before $T_{\text{snapshot}}$:
- **Monetary Merchandise Sales ($\text{M}_{\text{merch}}$):** $\sum_{j \in \mathcal{J}_c} \text{product\_sales}_j$
- **Monetary Shipping Charges ($\text{M}_{\text{ship}}$):** $\sum_{j \in \mathcal{J}_c} \text{shipping\_value}_j$
- **Monetary Discounts ($\text{M}_{\text{disc}}$):** $\sum_{j \in \mathcal{J}_c} \text{discount\_value}_j \le 0$
- **Monetary Returns / Cancellations ($\text{M}_{\text{ret}}$):** $\sum_{j \in \mathcal{J}_c} \text{cancellation\_value}_j \le 0$
- **Monetary Manual Adjustments ($\text{M}_{\text{man}}$):** $\sum_{j \in \mathcal{J}_c} \text{manual\_value}_j$
- **Monetary Administrative Settlements ($\text{M}_{\text{admin}}$):** $\sum_{j \in \mathcal{J}_c} \text{admin\_settlements\_value}_j$ (`CRUK`, `BANK CHARGES`, `ADJUST`, `ADJUST2`)
- **Primary Customer Commercial Net Spend ($\text{NetCommercialSpend}$):**
  $$\text{NetCommercialSpend}_c = \text{M}_{\text{merch}} + \text{M}_{\text{ship}} + \text{M}_{\text{disc}} + \text{M}_{\text{ret}} + \text{M}_{\text{man}}$$
- **Total Customer Account Balance ($\text{TotalAccountBalance}$):**
  $$\text{TotalAccountBalance}_c = \text{NetCommercialSpend}_c + \text{M}_{\text{admin}}$$
  *(Exact reconciliation to customer accounting ledger).*

### 3.6. Average Order Value (Conventional Retail AOV)
Calculated strictly across qualifying purchase orders:
$$\text{AOV}_c = \frac{\sum_{i \in \mathcal{I}_c} \text{qualifying\_gross\_sales}_i}{\text{Frequency}_c}$$
- Because every qualifying purchase has $\text{qualifying\_gross\_sales}_i > 0$, $\text{AOV}_c > 0$ for all qualifying customers.
- **Net Spend Per Order ($\text{NetSpendPerOrder}$):**
  $$\text{NetSpendPerOrder}_c = \frac{\text{NetCommercialSpend}_c}{\text{Frequency}_c}$$

---

## 4. Deterministic RFM Scoring Scheme

Scores are scaled from 1 to 5 (with 0 reserved for negative spend edge cases):

### 4.1. Recency Score ($R \in \{1, 2, 3, 4, 5\}$)
Lower elapsed days indicates higher engagement:
- Ranked quintiles:
  - Top 20% most recent: **5**
  - 20% – 40%: **4**
  - 40% – 60%: **3**
  - 60% – 80%: **2**
  - Bottom 20% (longest elapsed): **1**

### 4.2. Frequency Score ($F \in \{1, 2, 3, 4, 5\}$)
Because retail datasets exhibit heavy concentration at $F=1$ (~28–33% of customers), standard quantile binning collapses. To ensure 100% deterministic scoring and eliminate arbitrary tie-breaking:
- $F = 1 \implies \mathbf{1}$ (One-time customer)
- $F = 2 \implies \mathbf{2}$ (Repeat buyer / second order)
- $F \in \{3, 4\} \implies \mathbf{3}$ (Multi-order regular)
- $F \in \{5, 6, 7, 8\} \implies \mathbf{4}$ (Frequent buyer)
- $F \ge 9 \implies \mathbf{5}$ (High-frequency VIP buyer)

### 4.3. Monetary Score ($M \in \{0, 1, 2, 3, 4, 5\}$)
- If $\text{NetCommercialSpend}_c \le 0$: $M = \mathbf{0}$ (isolated into negative or zero spend segment).
- For customers with positive commercial spend ($\text{NetCommercialSpend}_c > 0$), scores 1 to 5 are assigned via ranked quintiles ($Q_{20}, Q_{40}, Q_{60}, Q_{80}$).

---

## 5. Monetary-Aware CRM Segmentation Framework (125-Cell Matrix)

Unlike simplified 2D RF grids, RetenSight implements a **genuinely monetary-aware** segmentation scheme where $M$ materially alters segment assignment across all 125 possible $(R, F, M)$ cells:

### 5.1. Key Business Rules
1. **Low-Value Cap on Champions**: A customer with $R \in [4, 5]$ and $F \in [4, 5]$ can only be a **Champion** if they also exhibit high monetary value ($M \in [4, 5]$). If $M=3$, they are classified as **Loyal Customers**; if $M \le 2$, they are classified as **Promising** (high engagement, low ticket size).
2. **Prioritization of High-Value Inactive Accounts**: Dormant accounts with $R \in [1, 2]$ and $F \ge 4$ are distinguished by spend:
   - High monetary spend ($M \in [4, 5]$) $\implies$ **Can't Lose Them** (VIP win-back priority).
   - Moderate/low spend ($M \le 3$) $\implies$ **At Risk** or **About To Sleep**.
3. **Value Differentiation for Lapsed Shoppers**: Lapsed accounts with $R \in [1, 2]$ and $F \in [2, 3]$:
   - High monetary spend ($M \ge 4$) $\implies$ **At Risk**.
   - Moderate/low spend ($M \le 3$) $\implies$ **About To Sleep** (if $R=2$) or **Hibernating** (if $R=1$).
4. **New vs Promising Shoppers**: Single-order buyers ($F=1$) with recent activity ($R \in [4, 5]$):
   - Higher spend ($M \ge 3$) $\implies$ **Promising**.
   - Low spend ($M \le 2$) $\implies$ **New Customers**.
5. **Deterministic & Exhaustive Coverage**: All 125 non-zero cells and the zero/negative spend condition are mutually exclusive and collectively exhaustive.

### 5.2. Complete 125-Cell Decision Table

| Segment Name | Recency ($R$) | Frequency ($F$) | Monetary ($M$) | Business Rationale & Outreach Action |
| :--- | :--- | :--- | :--- | :--- |
| **Champions** | $\{4, 5\}$ | $\{4, 5\}$ | $\{4, 5\}$ | Top-tier VIPs. High cadence and high spend. Concierge service, early catalog previews. |
| **Loyal Customers** | $\{4, 5\}$ | $\{4, 5\}$ | $\{3\}$ | High frequency with solid moderate spend. Upsell higher-margin product bundles. |
| **Loyal Customers** | $\{3\}$ | $\{4, 5\}$ | $\{3, 4, 5\}$ | Established repeat buyers. Loyalty rewards, automated re-order reminders. |
| **Loyal Customers** | $\{3, 4, 5\}$ | $\{3\}$ | $\{4, 5\}$ | Multi-order high spenders. Expand product category exposure. |
| **Potential Loyalists** | $\{4, 5\}$ | $\{2, 3\}$ | $\{2, 3, 4, 5\}$ | Recent repeat buyers showing growth. Category cross-sells, loyalty point incentives. |
| **New Customers** | $\{4, 5\}$ | $\{1\}$ | $\{1, 2\}$ | Recent entry-level one-time buyers. Product onboarding sequence, welcome nurture. |
| **Promising** | $\{4, 5\}$ | $\{1\}$ | $\{3, 4, 5\}$ | Recent high-ticket first-time buyers. White-glove second-order incentive. |
| **Promising** | $\{4, 5\}$ | $\{4, 5\}$ | $\{1, 2\}$ | High order cadence but very low basket spend. Margin-preserving bulk incentives. |
| **Promising** | $\{3\}$ | $\{1, 2\}$ | $\{3, 4, 5\}$ | Moderate recency high spenders. Seasonal catalog re-engagement. |
| **Can't Lose Them** | $\{1, 2\}$ | $\{4, 5\}$ | $\{4, 5\}$ | Former VIP high-spenders now dormant. Executive win-back outreach and bespoke offers. |
| **Can't Lose Them** | $\{1, 2\}$ | $\{3\}$ | $\{5\}$ | Former high-ticket regular buyers now lapsed. Personalized account reactivation. |
| **At Risk** | $\{1, 2\}$ | $\{4, 5\}$ | $\{1, 2, 3\}$ | Frequent buyers with low/mid spend who stopped ordering. Win-back reactivation surveys. |
| **At Risk** | $\{1, 2\}$ | $\{2, 3\}$ | $\{4, 5\}$ | Substantial historical spenders who have become inactive. Target with renewal incentives. |
| **About To Sleep** | $\{2\}$ | $\{1, 2, 3\}$ | $\{1, 2, 3\}$ | Fading engagement and modest historical spend. Low-cost automated discount nudges. |
| **About To Sleep** | $\{3\}$ | $\{1, 2\}$ | $\{1, 2\}$ | Mid-recency modest buyers. Gentle seasonal reminders. |
| **About To Sleep** | $\{3\}$ | $\{4, 5\}$ | $\{1, 2\}$ | Regular buyers slipping in recency with low basket size. Re-engagement reminders. |
| **Hibernating** | $\{1\}$ | $\{2, 3\}$ | $\{1, 2, 3\}$ | Lapsed repeat buyers with modest spend. Low-frequency broadcast email campaigns. |
| **Lost** | $\{1\}$ | $\{1\}$ | $\{1, 2, 3, 4, 5\}$ | Lapsed single-order customers inactive for over a year. Archive or broad remarketing. |
| **Negative / Zero Spend** | Any | Any | $\{0\}$ | Accounts with non-positive net commercial spend. Audit for excessive returns or defects. |

---

## 6. Chronological Evaluation Calendar & Observed 90-Day Repeat Rates

RetenSight maintains three strictly chronological evaluation cutoffs with fully observed 90-day forward windows, plus the final dataset end snapshot:

| Cutoff Date | Cutoff Timestamp | Forward Target Window | Total Days | Eligible Customers | Observed 90-Day Repeaters | Observed 90-Day Repeat Rate (%) |
| :--- | :--- | :--- | :---: | ---: | ---: | ---: |
| **Cutoff 1** | `2010-12-09 23:59:59` | `2010-12-10 00:00:00` to `2011-03-09 23:59:59` | 90 | 4,286 | 1,317 | **30.73%** |
| **Cutoff 2** | `2011-06-10 23:59:59` | `2011-06-11 00:00:00` to `2011-09-08 23:59:59` | 90 | 4,952 | 1,586 | **32.03%** |
| **Cutoff 3** | `2011-09-09 23:59:59` | `2011-09-10 00:00:00` to `2011-12-08 23:59:59` | 90 | 5,257 | 2,287 | **43.50%** |
| **Full History** | `2011-12-09 12:50:00` | Unobserved (Dataset End) | N/A | 5,853 | `<NA>` | **`<NA>` (Current CRM Snapshot)** |

### Calendar Integrity Notes
1. **Cutoff 3 Calibration**: Set to `2011-09-09 23:59:59` so that the 90-day forward window terminates at `2011-12-08 23:59:59`, leaving the dataset's final partial day (`2011-12-09`) strictly outside the target window. This ensures all 90 days are 100% observed and free of partial-day truncation bias.
2. **Observed Repeat Rates**: The 90-day repeat-purchase rate increases from 30.73% (Cutoff 1) and 32.03% (Cutoff 2) to 43.50% (Cutoff 3). These empirical rates reflect the observed transaction patterns across these specific 90-day forward windows.
3. **Target Exclusions**: The final history snapshot (`2011-12-09`) marks `repeat_purchase_90d` as `<NA>` and sets `is_target_window_observed = False`, completely preventing future target leakage into the production scoring table.
