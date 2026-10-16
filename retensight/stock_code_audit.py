"""Reproducible audit of special, administrative, and service stock codes.

Analyzes line counts, financial totals, customer attribution, transaction categories,
representative descriptions, and invoice samples to establish an evidence-based
classification and customer-spend treatment rule for each code.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from retensight.config import PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class StockCodeAuditEntry:
    """Audit entry for a specific stock code."""

    stock_code: str
    line_count: int
    total_value_gbp: float
    customer_attributed_lines: int
    customer_attributed_value_gbp: float
    unattributed_lines: int
    unattributed_value_gbp: float
    inferred_category: str
    is_physical_merchandise: bool
    increments_purchase_frequency: bool
    affects_customer_commercial_spend: bool
    treatment_rule: str
    evidence: str
    top_descriptions: Dict[str, int]
    sample_invoices: List[str]


# Knowledge-based evidence and treatment mapping for special and non-product stock codes
STOCK_CODE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "POST": {
        "inferred_category": "postage_and_shipping",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as special commercial charge. Shipping costs paid by customers affect customer "
            "commercial spend. Invoices containing only shipping fees (product_sales == 0) do not qualify "
            "as product repeat purchases."
        ),
        "evidence": (
            "Descriptions consist exclusively of 'POSTAGE'. High customer attribution (>95% of lines). "
            "Corresponds to standard customer shipping charges incurred during checkout."
        ),
    },
    "DOT": {
        "inferred_category": "website_delivery_fee",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as special commercial charge. Customer-attributed portion (16 lines, £11,906.36 "
            "on Customer 14096) represents delivery fees and affects commercial spend. Unattributed portion "
            "(£297,937.74) remains in whole-company financial reconciliation. Does not increment purchase frequency."
        ),
        "evidence": (
            "Descriptions consist of 'DOTCOM POSTAGE'. Batch fulfillment delivery fees for web orders. "
            "Overwhelmingly unattributed; customer-attributed lines belong to corporate partner account 14096."
        ),
    },
    "M": {
        "inferred_category": "manual_commercial_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as special commercial charge when positive, cancellation/credit when negative. "
            "Adjusts customer commercial net spend (custom bespoke billing / concession). "
            "Does not count as a standard catalog merchandise repeat purchase."
        ),
        "evidence": (
            "Description is 'Manual'. Manually keyed administrative corrections, price adjustments, and "
            "bespoke wholesale charges without specific merchandise catalog SKU identification."
        ),
    },
    "D": {
        "inferred_category": "commercial_discount",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as commercial discount. Reduces customer commercial net spend. "
            "Does not increment purchase frequency."
        ),
        "evidence": (
            "Description is 'Discount'. Commercial concessions and rebates granted to trade accounts. "
            "Transactions reduce customer account balance."
        ),
    },
    "BANK CHARGES": {
        "inferred_category": "banking_and_payment_fee",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as administrative financial fee. Excluded from customer commercial spend "
            "(isolated under administrative settlements, +£330.00 customer total). "
            "Preserved in business-level financial audit. Excluded from repeat purchase frequency."
        ),
        "evidence": (
            "Description is 'Bank Charges'. Wire transfer fees, international payment processing charges, "
            "and merchant operational overhead."
        ),
    },
    "CRUK": {
        "inferred_category": "charity_commission",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as administrative charity commission payout. Excluded from customer commercial spend "
            "(isolated under administrative settlements, -£7,933.43). All 16 transactions belong to Customer ID 14096 "
            "(Cancer Research UK). Preserved in business-level financial audit."
        ),
        "evidence": (
            "Description is 'CRUK Commission'. Payouts / commission disbursements to charity partner Customer 14096, "
            "not merchandise purchases or customer returns."
        ),
    },
    "ADJUST": {
        "inferred_category": "staff_clerical_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as internal staff clerical adjustment. Excluded from customer commercial spend "
            "(isolated under administrative settlements, +£2,038.12 net customer total). "
            "Preserved in business-level financial audit."
        ),
        "evidence": (
            "Descriptions specify internal staff adjustments (e.g., 'Adjustment by john on 26/01/2010'). "
            "Internal book balance corrections by warehouse/accounting personnel."
        ),
    },
    "ADJUST2": {
        "inferred_category": "staff_clerical_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as internal staff clerical adjustment. Excluded from customer commercial spend "
            "(isolated under administrative settlements, +£731.05 customer total). "
            "Preserved in business-level financial audit."
        ),
        "evidence": (
            "Descriptions specify internal staff corrections ('Adjustment by Peter on Jun 25 2010'). "
            "Internal book balance correction."
        ),
    },
    "B": {
        "inferred_category": "bad_debt_writeoff",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as bad_debt_adjustment. Separated completely from customer commercial revenue. "
            "Company-level accounting write-off of uncollectible balances (-£147,614.08). Excluded from customer RFM."
        ),
        "evidence": (
            "Description is 'Adjust bad debt'. Invoices are prefixed with 'A' (e.g. A506401). "
            "0 customer attribution."
        ),
    },
    "AMAZONFEE": {
        "inferred_category": "marketplace_platform_fee",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as marketplace platform fee. 100% unattributed. Excluded from customer RFM; "
            "retained in company-level financial audit."
        ),
        "evidence": (
            "Description is 'AMAZON FEE'. Deductions taken by Amazon marketplace platform for third-party seller fees."
        ),
    },
    "S": {
        "inferred_category": "product_sample_writeoff",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as sample adjustment. Completely unattributed. Excluded from customer RFM."
        ),
        "evidence": (
            "Description is 'SAMPLES'. Internal sample distributions and write-offs. Quantity negative, 0 customer attribution."
        ),
    },
    "PADS": {
        "inferred_category": "physical_merchandise",
        "is_physical_merchandise": True,
        "increments_purchase_frequency": True,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as standard catalog physical merchandise. Description confirms physical cushion inserts "
            "('PADS TO MATCH ALL CUSHIONS'). Ordered alongside cushion covers in multi-line customer orders. "
            "Positive lines are classified as standard_product_sale; returns as standard merchandise returns."
        ),
        "evidence": (
            "Description is 'PADS TO MATCH ALL CUSHIONS'. Every invoice containing PADS is a multi-line customer order "
            "containing 11 to 93 other home decor items."
        ),
    },
    "GIFT": {
        "inferred_category": "inventory_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as inventory adjustment. Price is £0.00, customer ID is missing. Excluded from customer RFM."
        ),
        "evidence": (
            "Zero price administrative inventory movement without customer transaction value."
        ),
    },
    "DCGSSBOY": {
        "inferred_category": "physical_merchandise",
        "is_physical_merchandise": True,
        "increments_purchase_frequency": True,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as standard product merchandise. Walk-in / unattributed sales of boys party bags."
        ),
        "evidence": (
            "Description is 'BOYS PARTY BAG'. Tangible party goods sold at standard retail unit prices."
        ),
    },
    "DCGSSGIRL": {
        "inferred_category": "physical_merchandise",
        "is_physical_merchandise": True,
        "increments_purchase_frequency": True,
        "affects_customer_commercial_spend": True,
        "treatment_rule": (
            "Classified as standard product merchandise. Walk-in / unattributed sales of girls party bags."
        ),
        "evidence": (
            "Description is 'GIRLS PARTY BAG'. Tangible party goods sold at standard retail unit prices."
        ),
    },
    "DCGSLBOY": {
        "inferred_category": "inventory_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as inventory adjustment. Price is £0.00. Excluded from customer RFM."
        ),
        "evidence": (
            "Zero price inventory entry without customer attribution."
        ),
    },
    "DCGSLGIRL": {
        "inferred_category": "inventory_adjustment",
        "is_physical_merchandise": False,
        "increments_purchase_frequency": False,
        "affects_customer_commercial_spend": False,
        "treatment_rule": (
            "Classified as inventory adjustment. Price is £0.00. Excluded from customer RFM."
        ),
        "evidence": (
            "Zero price inventory entry without customer attribution."
        ),
    },
}


def audit_special_stock_codes(
    df: pd.DataFrame,
    target_codes: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Produces an exhaustive audit of special and administrative stock codes.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned transactions DataFrame.
    target_codes : Optional[Sequence[str]]
        Specific codes to audit. If None, audits all codes configured in PipelineConfig
        plus other known alpha codes.

    Returns
    -------
    Dict[str, Any]
        Audit summary dictionary containing structured entries and totals.
    """
    if target_codes is None:
        target_codes = sorted(
            list(
                set(
                    list(PipelineConfig.special_stock_codes)
                    + list(STOCK_CODE_TAXONOMY.keys())
                )
            )
        )

    logger.info("Auditing %d special and candidate stock codes...", len(target_codes))

    entries: List[StockCodeAuditEntry] = []
    total_lines_all = 0
    total_value_all = 0.0

    for code in target_codes:
        sub = df[df["stock_code"] == code]
        if len(sub) == 0:
            continue

        line_count = int(len(sub))
        total_val = float(round(sub["line_total"].sum(), 2))
        total_lines_all += line_count
        total_value_all += total_val

        attr_sub = sub[sub["has_customer_id"]]
        attr_lines = int(len(attr_sub))
        attr_val = float(round(attr_sub["line_total"].sum(), 2))

        unattr_lines = line_count - attr_lines
        unattr_val = float(round(total_val - attr_val, 2))

        top_desc = (
            sub["description"]
            .replace("", "[BLANK]")
            .value_counts()
            .head(3)
            .to_dict()
        )
        sample_invoices = sub["invoice"].drop_duplicates().head(3).tolist()

        tax_info = STOCK_CODE_TAXONOMY.get(
            code,
            {
                "inferred_category": "ambiguous_or_unclassified",
                "is_physical_merchandise": False,
                "increments_purchase_frequency": False,
                "affects_customer_commercial_spend": False,
                "treatment_rule": "Subject to review; excluded from customer repeat purchase frequency.",
                "evidence": "No documented taxonomy entry available.",
            },
        )

        entry = StockCodeAuditEntry(
            stock_code=code,
            line_count=line_count,
            total_value_gbp=total_val,
            customer_attributed_lines=attr_lines,
            customer_attributed_value_gbp=attr_val,
            unattributed_lines=unattr_lines,
            unattributed_value_gbp=unattr_val,
            inferred_category=tax_info["inferred_category"],
            is_physical_merchandise=tax_info["is_physical_merchandise"],
            increments_purchase_frequency=tax_info["increments_purchase_frequency"],
            affects_customer_commercial_spend=tax_info["affects_customer_commercial_spend"],
            treatment_rule=tax_info["treatment_rule"],
            evidence=tax_info["evidence"],
            top_descriptions=top_desc,
            sample_invoices=sample_invoices,
        )
        entries.append(entry)

    # Compile summary totals
    audit_dict = {
        "audit_metadata": {
            "audited_codes_count": len(entries),
            "total_lines_analyzed": total_lines_all,
            "total_value_gbp": round(total_value_all, 2),
        },
        "stock_code_entries": [asdict(e) for e in entries],
    }

    return audit_dict


def save_stock_code_audit_reports(
    audit_dict: Dict[str, Any],
    json_path: Path = Path("reports/special_stock_codes_audit.json"),
    md_path: Path = Path("reports/special_stock_codes_audit.md"),
) -> None:
    """Exports the stock code audit to structured JSON and human-readable Markdown.

    Parameters
    ----------
    audit_dict : Dict[str, Any]
        Audit dictionary returned by `audit_special_stock_codes`.
    json_path : Path
        Output destination for JSON report.
    md_path : Path
        Output destination for Markdown report.
    """
    json_path = Path(json_path)
    md_path = Path(md_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_dict, f, indent=2)
    logger.info("Saved special stock code audit JSON to '%s'.", json_path)

    # 2. Save a concise Markdown summary. The JSON file retains the complete audit details.
    entries = audit_dict["stock_code_entries"]
    meta = audit_dict["audit_metadata"]

    md_lines = [
        "# RetenSight — Special Stock Code & Service Fee Audit Report",
        "",
        f"RetenSight reviewed **{meta['audited_codes_count']} stock codes** across **{meta['total_lines_analyzed']:,} lines**, with a combined audited value of **£{meta['total_value_gbp']:,.2f}**. The audit separates physical products, commercial fees and administrative entries so they do not distort purchase frequency or customer spend.",
        "",
        "## Audited codes",
        "",
        "| Code | Lines | Total value (£) | Category | Merchandise? | Counts as purchase? | Included in customer commercial spend? |",
        "|---|---:|---:|---|:---:|:---:|:---:|",
    ]

    for e in entries:
        merchandise = "Yes" if e["is_physical_merchandise"] else "No"
        frequency = "Yes" if e["increments_purchase_frequency"] else "No"
        spend = "Yes" if e["affects_customer_commercial_spend"] else "No"
        md_lines.append(
            f"| {e['stock_code']} | {e['line_count']:,} | £{e['total_value_gbp']:,.2f} | "
            f"{e['inferred_category']} | {merchandise} | {frequency} | {spend} |"
        )

    md_lines.extend([
        "",
        "## Rules that matter for CRM",
        "",
        "- POST and DOT are commercial shipping fees. They affect spend but do not count as merchandise purchases on their own.",
        "- M and D adjust commercial spend but do not increase purchase frequency.",
        "- CRUK, BANK CHARGES, ADJUST and ADJUST2 are administrative settlements. They are reported separately from customer commercial spend.",
        "- B records bad debt and stays in company-level accounting.",
        "- PADS, DCGSSBOY and DCGSSGIRL are treated as physical merchandise.",
        "- Unattributed fees such as AMAZONFEE and sample write-offs remain in the company audit but are not assigned to customer RFM profiles.",
        "",
        "This Markdown file is the short report. The companion JSON audit retains detailed evidence, descriptions and sample invoices for each code.",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    logger.info("Saved special stock code audit Markdown to '%s'.", md_path)
