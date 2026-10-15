# RetenSight — Worker Contract

You are the implementation worker. Follow this specification literally. The project owner decides analytical scope and accepts or rejects each completed increment.

## Objective
Build a complete e-commerce CRM analytics and decision-support system from the locally supplied UCI Online Retail II workbook. The business goals are customer understanding, RFM segmentation, 90-day repeat-purchase propensity, and explainable customer-priority queues under limited outreach capacity. Deliver a verified, interactive Power BI report.

## Non-negotiable constraints
- Keep the supplied raw workbook unchanged and never commit it.
- Normal CPU only. No GPU, paid APIs, or paid software requirements.
- Do not invent metrics, test results, model performance, UI states, or completed work.
- Do not claim causal campaign uplift from observational transaction data.
- Do not use future information in features. All scoring features must be available as of the scoring cutoff; labels must use a complete future 90-day period.
- The owner reviews pushed commits. Work in small, complete increments and stop for review after each requested increment.
- Cite and acknowledge existing code/method references in project documentation. Reproducing methods is fine; never claim that established algorithms or copied code were invented here.
- Write technical docs needed to run the project. Defer the polished academic report and presentation until the owner confirms that implementation and dashboard outputs are frozen.
- Do not populate user-facing documents with repetitive phase/step labels.

## Data rules
The workbook is expected at `data/raw/online_retail_II.xlsx` or project root if initially supplied there. Detect both sheets and validate their names/schema. The two sheets overlap in date coverage: correct only verified cross-sheet full-row duplicate copies. Do not drop all rows in the overlapping date range, and do not indiscriminately deduplicate within a sheet. Keep a data lineage/cleaning audit.
- Normalize column names and dtypes.
- Customer-level modeling excludes rows without customer IDs but preserve a separate reconciliation for unattributed business sales.
- Handle cancellation invoices, nonpositive quantities/prices, and non-product codes through documented, configurable rules.
- Calculate line value as quantity × price; clearly distinguish gross positive sales, cancellations/returns, and net revenue.
- Aggregate line items to invoice and customer grain before joining summaries; add uniqueness and reconciliation checks to prevent fanout.
- Output counts and value totals at each cleaning stage.

## Models and evaluation
- RFM baseline plus expanded logistic-regression model, with deterministic preprocessing and seeds.
- Establish target: at least one purchase in the 90 days following a cutoff.
- Keep all features as-of cutoff. Exclude a customer if the full target window is unavailable. Define how same-day invoices are aggregated.
- Maintain the three chronological evaluation cutoffs currently specified in the project planning material, if the target windows are fully observed. Document the exact cutoffs and windows.
- Report ROC-AUC, average precision, Brier score/calibration, top-decile purchase precision and bottom-decile non-purchase rate. Compare model metrics and business utility; no model must be declared a winner for every decision.
- Tune on training/validation data only. Holdout windows are not used for hyperparameter selection.
- Compare risk-first, value-aware, and hybrid CRM queue policies at fixed capacities (e.g. 1%, 5%, 10%, 20%) against a random/first-come baseline. Historical value is not CLV or profit.
- Explain features/scores in customer-facing business terms. Check stability across windows and run sensitivity tests.
- CLV is optional and outside the core unless it independently beats simple baselines on temporal holdout evaluation and implementation discrepancy checks are resolved.

## Engineering requirements
- Modular Python package, pinned/bounded dependencies, configuration, type hints where useful, logging, error handling, deterministic runs and relative paths.
- Provide one documented command for ingestion through validation and output generation.
- Automated tests: workbook/schema; cross-sheet duplicate correction; cleaning rules; row/invoice/customer grain; revenue reconciliation; date cutoffs/90-day boundaries; feature leakage; output metrics; queue capacity.
- Run the full workbook, not just samples. Unit-test fixtures may be small. Clearly differentiate fixture tests from full-data results.
- Use local output directories and ignore workbook, caches, virtual env, and machine-specific files in Git.
- Provide machine-readable output validation that fails on discrepancies.
- Power BI must use clean import tables, a star schema or explicitly justified relationships, measures, slicers, drill-through/customer details and clear labels. Dashboard KPIs must reconcile to Python outputs.
- Create/validate a native PBIX in Power BI Desktop where possible. Never fake a PBIX by renaming another file. If this runtime cannot create PBIX, state the precise blocker and provide ready-to-import files, DAX, theme, model diagram, and detailed build instructions.

## Git protocol
Before editing, inspect repository state and avoid overwriting existing work. Commit each completed increment with a descriptive message and push to the connected remote. Keep dataset and derived files out of Git unless owner explicitly approves specific small, non-sensitive deliverables. After each increment hand off: commit hash, paths changed, exact commands, tests and results, known issues. Stop for owner review.

## First assignment
Implement only the data ingestion/cleaning foundation:
1. Inspect workspace and locate workbook; do not download another dataset.
2. Scaffold package, dependency file, config, .gitignore, data dictionary skeleton.
3. Implement full-workbook ingestion and safe cross-sheet duplicate handling.
4. Produce a cleaning audit and invoice-level cleaned table locally.
5. Add unit tests for duplicate handling, cleaning rules, schema, and revenue/count invariants.
6. Run unit tests and full data processing on the actual workbook.
7. Commit and push. Stop; do not start modeling until owner review.
