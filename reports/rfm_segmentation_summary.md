# Customer RFM Summary

RFM uses Recency, Frequency and Monetary value to describe customer purchase history. RetenSight assigns eligible customers to one of 11 segments using a deterministic decision table.

## Repeat-purchase outcomes

A repeat purchase means at least one qualifying merchandise purchase in the following 90 days. Outcomes are shown only where the full window is observed.

| Snapshot date | Customers | Repeaters in next 90 days | Repeat rate | Target observed? |
|---|---:|---:|---:|---|
| 2010-12-09 | 4,286 | 1,317 | 30.73% | Yes |
| 2011-06-10 | 4,952 | 1,586 | 32.03% | Yes |
| 2011-09-09 | 5,257 | 2,287 | 43.50% | Yes |
| 2011-12-09 | 5,853 | — | Not observed | No |

## Segment distribution at 2011-12-09

The latest snapshot contains 5,853 customers. Its future 90-day outcome is not observed, so this section describes segments only.

| Segment | Customers | Share |
|---|---:|---:|
| Champions | 1,257 | 21.5% |
| About To Sleep | 1,088 | 18.6% |
| Loyal Customers | 937 | 16.0% |
| Lost | 695 | 11.9% |
| Potential Loyalists | 507 | 8.7% |
| At Risk | 458 | 7.8% |
| Hibernating | 253 | 4.3% |
| Can't Lose Them | 215 | 3.7% |
| Promising | 211 | 3.6% |
| New Customers | 207 | 3.5% |
| Negative or Zero Spend | 25 | 0.4% |

## RFM definitions

- **Recency:** days since the latest qualifying purchase; lower is more recent.
- **Frequency:** number of distinct qualifying purchase invoices.
- **Monetary value:** customer commercial net spend, including commercial returns and adjustments but excluding administrative settlements and bad debt.
- Positive spend is ranked into five monetary groups. Zero or negative spend receives a separate score and segment.

The 126-row segmentation decision table is the source of truth for all score combinations: [CSV](crm_segment_decision_table.csv) and [JSON](crm_segment_decision_table.json).

## Interpretation

Segments summarize past behaviour and help organize CRM planning; they do not prove campaign impact. The final December 2011 snapshot has no observed future target and must not be treated as a zero repeat rate.
