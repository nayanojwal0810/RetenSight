"""Unit tests for special stock code audit and categorization."""

from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pytest

from retensight.stock_code_audit import (
    STOCK_CODE_TAXONOMY,
    audit_special_stock_codes,
    save_stock_code_audit_reports,
)


@pytest.fixture
def sample_transactions_for_audit() -> pd.DataFrame:
    """Creates a synthetic transaction DataFrame containing diverse special stock codes."""
    records = [
        # POST: customer shipping charge
        {
            "invoice": "10001",
            "stock_code": "POST",
            "description": "POSTAGE",
            "quantity": 1,
            "invoice_date": pd.Timestamp("2010-01-10 10:00:00"),
            "price": 18.0,
            "customer_id": 12345,
            "country": "United Kingdom",
            "line_total": 18.0,
            "has_customer_id": True,
            "transaction_category": "special_commercial_charge",
        },
        # DOT: unattributed dotcom postage
        {
            "invoice": "10002",
            "stock_code": "DOT",
            "description": "DOTCOM POSTAGE",
            "quantity": 1,
            "invoice_date": pd.Timestamp("2010-01-10 11:00:00"),
            "price": 250.0,
            "customer_id": pd.NA,
            "country": "United Kingdom",
            "line_total": 250.0,
            "has_customer_id": False,
            "transaction_category": "special_commercial_charge",
        },
        # PADS: physical cushion pads merchandise
        {
            "invoice": "10003",
            "stock_code": "PADS",
            "description": "PADS TO MATCH ALL CUSHIONS",
            "quantity": 2,
            "invoice_date": pd.Timestamp("2010-01-11 12:00:00"),
            "price": 10.0,
            "customer_id": 12346,
            "country": "United Kingdom",
            "line_total": 20.0,
            "has_customer_id": True,
            "transaction_category": "standard_product_sale",
        },
        # D: commercial discount
        {
            "invoice": "C10004",
            "stock_code": "D",
            "description": "Discount",
            "quantity": -1,
            "invoice_date": pd.Timestamp("2010-01-12 13:00:00"),
            "price": 50.0,
            "customer_id": 12347,
            "country": "United Kingdom",
            "line_total": -50.0,
            "has_customer_id": True,
            "transaction_category": "cancellation",
        },
        # B: bad debt writeoff
        {
            "invoice": "A10005",
            "stock_code": "B",
            "description": "Adjust bad debt",
            "quantity": 1,
            "invoice_date": pd.Timestamp("2010-01-13 14:00:00"),
            "price": -1000.0,
            "customer_id": pd.NA,
            "country": "United Kingdom",
            "line_total": -1000.0,
            "has_customer_id": False,
            "transaction_category": "bad_debt_adjustment",
        },
    ]
    return pd.DataFrame(records)


def test_audit_special_stock_codes_invariants(sample_transactions_for_audit: pd.DataFrame) -> None:
    """Verifies that audit calculates line counts, financial totals, and attribution splits accurately."""
    audit = audit_special_stock_codes(sample_transactions_for_audit)
    entries = {e["stock_code"]: e for e in audit["stock_code_entries"]}

    assert "POST" in entries
    assert "DOT" in entries
    assert "PADS" in entries
    assert "D" in entries
    assert "B" in entries

    # POST checks
    post_e = entries["POST"]
    assert post_e["line_count"] == 1
    assert post_e["customer_attributed_lines"] == 1
    assert post_e["unattributed_lines"] == 0
    assert post_e["total_value_gbp"] == 18.0
    assert post_e["is_physical_merchandise"] is False
    assert post_e["increments_purchase_frequency"] is False

    # DOT checks
    dot_e = entries["DOT"]
    assert dot_e["line_count"] == 1
    assert dot_e["customer_attributed_lines"] == 0
    assert dot_e["unattributed_lines"] == 1
    assert dot_e["total_value_gbp"] == 250.0
    assert dot_e["is_physical_merchandise"] is False

    # PADS checks (confirmed physical merchandise)
    pads_e = entries["PADS"]
    assert pads_e["line_count"] == 1
    assert pads_e["is_physical_merchandise"] is True
    assert pads_e["increments_purchase_frequency"] is True
    assert "CUSHIONS" in pads_e["evidence"]

    # Attribution reconciliation invariant
    for e in audit["stock_code_entries"]:
        assert e["line_count"] == e["customer_attributed_lines"] + e["unattributed_lines"]
        assert np.isclose(
            e["total_value_gbp"],
            e["customer_attributed_value_gbp"] + e["unattributed_value_gbp"],
            atol=0.01,
        )


def test_save_stock_code_audit_reports(sample_transactions_for_audit: pd.DataFrame) -> None:
    """Verifies report file generation and non-empty content."""
    audit = audit_special_stock_codes(sample_transactions_for_audit)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        json_file = tmp_path / "audit.json"
        md_file = tmp_path / "audit.md"

        save_stock_code_audit_reports(audit, json_path=json_file, md_path=md_file)

        assert json_file.exists()
        assert md_file.exists()
        assert json_file.stat().st_size > 0
        assert md_file.stat().st_size > 0

        content = md_file.read_text(encoding="utf-8")
        assert "# RetenSight — Special Stock Code & Service Fee Audit Report" in content
        assert "POST" in content
        assert "PADS" in content
