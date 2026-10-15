# RetenSight

E-commerce CRM decision support for customer segmentation, repeat-purchase propensity, and explainable retention prioritization.

## Current status
Repository setup only. The implementation worker should follow [AGENTS.md](AGENTS.md). The first deliverable is a full-data, audited cleaning pipeline and its tests. Predictive models and Power BI come after the owner accepts the data layer.

## Data
Use the owner-provided UCI Online Retail II workbook locally. Do not commit the raw workbook or fetch a replacement dataset silently. See `.gitignore` and [AGENTS.md](AGENTS.md) for data requirements.

## Design principles
- Real full-dataset results; no fabricated or sample-derived headline metrics.
- Leakage-safe chronological evaluation.
- Compare RFM and expanded models against simple baselines.
- Explain CRM actions and trade-offs; do not claim causal retention lift.
- CPU-only, reproducible, testable engineering.
- Cite existing references and reproduce them transparently.

## Reference implementation
The project uses established methods and references existing implementations, including [e-commerce churn/CLV prediction](https://github.com/ruturajdixit99/ecommerce-churn-clv-prediction). RetenSight's value should come from validated implementation, data-quality corrections, temporal evaluation, explainability, and a usable Power BI decision interface—not claims that established methods were invented here.
