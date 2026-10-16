# RetenSight — Project Working Rules

## Purpose

RetenSight is an e-commerce CRM decision-support project. It cleans transaction data, builds customer RFM profiles and segments, estimates 90-day repeat-purchase likelihood, and compares contact-prioritization strategies. The deliverable is a tested Streamlit dashboard and clear supporting documentation.

## Work carefully

- Inspect the current code and artifacts before editing.
- Make focused changes and commit them to the intended branch.
- Never commit the raw workbook, credentials, personal exports, caches, or large intermediate files.
- Do not invent data, results, tests, screenshots, or deployment status.
- Do not change model logic just to improve the presentation.
- Keep the code readable and the user interface concise.
- Use plain, formal English in user-facing documentation.
- Keep internal development stages out of the dashboard navigation.
- Use the correct cohort and fully observed target window for every model comparison.
- Represent unobserved outcomes as missing, never as zero.
- Separate company-wide accounting totals from customer-attributed commercial spend.
- Do not claim campaign uplift, saved revenue, profit, churn prevention, or causal impact from observational transactions.

## Data rules

- Source workbook: `data/raw/online_retail_II.xlsx`.
- The two source sheets overlap. Remove only verified cross-sheet duplicate copies; preserve legitimate repeated lines within each sheet.
- Keep unattributed transactions in company-level reconciliation, but exclude them from customer-level modelling.
- Define qualifying purchase events at invoice level, not line-item level.
- Keep sales, returns, fees, administrative adjustments and bad debt distinguishable.
- Preserve audit outputs and reconcile invoice/customer totals.

## Models and evaluation

- Keep the RFM logistic-regression baseline and expanded logistic-regression challenger.
- Use only features available at the scoring date.
- The target is at least one qualifying purchase in the following 90 days.
- The June 2011 cohort governs the main model recommendation. The September 2011 cohort is retrospective because it was inspected during development.
- Compare Risk-first, Value-aware and Hybrid queues at equal capacity and include the random benchmark.
- Historical queue spend is not proof of campaign impact.

## Checks and handoff

After changes, run the relevant tests and report the exact outcome. For dashboard changes, run the dashboard tests, fast suite and Streamlit execution check. Inspect rendered screenshots when available; never say visual review is complete unless it happened. Keep README commands and generated report descriptions aligned with the actual code.
