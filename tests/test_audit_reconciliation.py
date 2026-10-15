"""Unit tests for pipeline audit generation and reconciliation invariant enforcement."""

import json
from pathlib import Path
import pytest

from retensight.aggregation import build_invoice_aggregates
from retensight.audit import generate_markdown_report, generate_pipeline_audit, save_audit_reports
from retensight.cleaning import clean_and_classify_transactions
from retensight.deduplication import resolve_cross_sheet_duplicates


def test_audit_generation_and_invariants(synthetic_sheets):
    """Verifies that all pipeline invariants pass on consistent data and measures are clearly defined."""
    df1, df2 = synthetic_sheets
    combined, dedup_audit = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    audit = generate_pipeline_audit(dedup_audit, cleaned, invoices)

    assert "ingestion" in audit
    assert "deduplication" in audit
    assert "transactions_breakdown" in audit
    assert "invoice_breakdown" in audit
    assert "financial_reconciliation" in audit
    assert "reconciliation_invariants" in audit

    # Verify distinct financial measures
    fin = audit["financial_reconciliation"]
    assert "gross_product_sales_gbp" in fin
    assert "special_commercial_charges_gbp" in fin
    assert "gross_sales_gbp" in fin
    assert "cancellations_value_gbp" in fin
    assert "net_commercial_value_gbp" in fin
    assert "bad_debt_adjustments_gbp" in fin
    assert "all_transactions_net_value_gbp" in fin

    # Verify customer-ready vs attributed count invariant
    tx = audit["transactions_breakdown"]
    assert tx["customer_commercial_ready_transactions"] == (
        tx["customer_attributed_transactions"] - tx["promotional_freebies_count"]
    )

    # Check all invariants are True
    for inv_name, status in audit["reconciliation_invariants"].items():
        assert status is True, f"Invariant failed: {inv_name}"


def test_audit_invariant_failure_detection(synthetic_sheets):
    """Verifies that tampering with numbers triggers a ValueError in invariant checking."""
    df1, df2 = synthetic_sheets
    combined, dedup_audit = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)

    # Tamper with invoice line_count to simulate fanout or lost record
    tampered_invoices = invoices.copy()
    tampered_invoices.loc[0, "line_count"] += 999

    with pytest.raises(ValueError, match="CRITICAL RECONCILIATION INVARIANT FAILED"):
        generate_pipeline_audit(dedup_audit, cleaned, tampered_invoices)


def test_audit_reports_export(synthetic_sheets, tmp_path):
    """Verifies JSON and Markdown report export."""
    df1, df2 = synthetic_sheets
    combined, dedup_audit = resolve_cross_sheet_duplicates(df1, df2)
    cleaned = clean_and_classify_transactions(combined)
    invoices = build_invoice_aggregates(cleaned)
    audit = generate_pipeline_audit(dedup_audit, cleaned, invoices)

    json_file = tmp_path / "audit.json"
    md_file = tmp_path / "audit.md"

    save_audit_reports(audit, json_file, md_file)

    assert json_file.exists()
    assert md_file.exists()

    with open(json_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["transactions_breakdown"]["total_retained_transactions"] == len(cleaned)

    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "RetenSight" in md_text
    assert "PASSED [✓]" in md_text
    assert "Gross Product Sales" in md_text
    assert "Special Commercial Charges" in md_text
