"""Data normalization, cleaning, and transaction categorization."""

import logging
from typing import Sequence

import numpy as np
import pandas as pd

from retensight.config import PipelineConfig

logger = logging.getLogger(__name__)


def clean_and_classify_transactions(
    df: pd.DataFrame,
    special_stock_codes: Sequence[str] = PipelineConfig.special_stock_codes,
) -> pd.DataFrame:
    """Normalizes column names, casts data types, computes line totals,

    and assigns transparent transaction classification flags.

    Parameters
    ----------
    df : pd.DataFrame
        Raw or deduplicated transaction DataFrame.
    special_stock_codes : Sequence[str]
        Set of known non-product administrative stock codes.

    Returns
    -------
    pd.DataFrame
        Cleaned and enriched DataFrame.
    """
    logger.info("Normalizing columns and types for %d rows...", len(df))
    cleaned = df.copy()

    # 1. Normalize column names to snake_case
    column_mapping = {
        "Invoice": "invoice",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "price",
        "Customer ID": "customer_id",
        "Country": "country",
    }
    cleaned = cleaned.rename(columns=column_mapping)

    # 2. String normalization
    cleaned["invoice"] = cleaned["invoice"].astype(str).str.strip()
    cleaned["stock_code"] = cleaned["stock_code"].astype(str).str.strip().str.upper()
    cleaned["description"] = cleaned["description"].fillna("").astype(str).str.strip()
    cleaned["country"] = cleaned["country"].fillna("Unspecified").astype(str).str.strip()

    # 3. Numeric and date normalization
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="raise").astype("int64")
    cleaned["price"] = pd.to_numeric(cleaned["price"], errors="raise").astype("float64")
    cleaned["invoice_date"] = pd.to_datetime(cleaned["invoice_date"], errors="raise")

    # Customer ID: cast to pandas nullable integer Int64 (preserves NA without float representation)
    cleaned["customer_id"] = pd.to_numeric(cleaned["customer_id"], errors="coerce").astype("Int64")

    # 4. Line total calculation
    cleaned["line_total"] = (cleaned["quantity"] * cleaned["price"]).round(2)

    # 5. Core classification flags
    cleaned["is_cancellation"] = cleaned["invoice"].str.startswith("C", na=False)
    cleaned["is_bad_debt"] = cleaned["invoice"].str.startswith("A", na=False)
    cleaned["is_zero_price"] = cleaned["price"] == 0.0
    cleaned["is_negative_price"] = cleaned["price"] < 0.0
    cleaned["has_customer_id"] = cleaned["customer_id"].notna()
    cleaned["is_special_code"] = cleaned["stock_code"].isin(set(special_stock_codes))

    # 6. Granular transaction categorization
    # Rules are evaluated deterministically in priority order
    conditions = [
        cleaned["is_bad_debt"],
        cleaned["is_cancellation"],
        cleaned["is_zero_price"] & cleaned["has_customer_id"],
        cleaned["is_zero_price"] & (~cleaned["has_customer_id"]),
        (cleaned["quantity"] > 0) & (cleaned["price"] > 0) & (~cleaned["is_cancellation"]) & cleaned["is_special_code"],
        (cleaned["quantity"] > 0) & (cleaned["price"] > 0) & (~cleaned["is_cancellation"]) & (~cleaned["is_special_code"]),
    ]
    categories = [
        "bad_debt_adjustment",
        "cancellation",
        "promotional_freebie",
        "inventory_adjustment",
        "special_commercial_charge",
        "standard_product_sale",
    ]
    cleaned["transaction_category"] = np.select(conditions, categories, default="other_anomaly")

    # 7. Customer analysis, commercial spend, and modeling readiness flags
    cleaned["is_shipping"] = cleaned["stock_code"].isin(set(PipelineConfig.shipping_stock_codes))
    cleaned["is_discount"] = cleaned["stock_code"].isin(set(PipelineConfig.discount_stock_codes))
    cleaned["is_manual"] = cleaned["stock_code"].isin(set(PipelineConfig.manual_stock_codes))
    cleaned["is_admin_settlement"] = cleaned["stock_code"].isin(set(PipelineConfig.administrative_stock_codes))
    cleaned["is_merchandise"] = (~cleaned["is_special_code"]) & (~cleaned["is_bad_debt"])

    # Line item qualifies as a physical merchandise purchase
    cleaned["qualifies_as_purchase_item"] = (
        cleaned["is_merchandise"]
        & (~cleaned["is_cancellation"])
        & (cleaned["quantity"] > 0)
        & (cleaned["price"] > 0)
    )

    # Line item represents a physical merchandise return / cancellation
    cleaned["is_merchandise_return"] = (
        cleaned["is_merchandise"]
        & cleaned["is_cancellation"]
        & (~cleaned["is_zero_price"])
    )

    # Anomaly flag: line item on a cancellation invoice with positive value
    cleaned["is_positive_cancellation_anomaly"] = (
        cleaned["is_cancellation"] & (cleaned["line_total"] > 0)
    )

    # Line item affects customer commercial spend (excludes non-commercial admin settlements, bad debt, freebies)
    cleaned["affects_customer_commercial_spend"] = (
        cleaned["has_customer_id"]
        & (~cleaned["is_bad_debt"])
        & (~cleaned["is_admin_settlement"])
        & (~cleaned["is_zero_price"])
    )

    # Full customer attribution flag: all rows with valid customer ID (including freebies)
    cleaned["is_customer_attributed"] = cleaned["has_customer_id"]

    # Commercial customer readiness flag (model-ready):
    # Excludes zero-revenue promotional freebies and administrative adjustments.
    # Preserves paid product sales, special commercial charges, and cancellations.
    cleaned["is_commercial_customer_ready"] = (
        cleaned["has_customer_id"]
        & cleaned["transaction_category"].isin(
            ["standard_product_sale", "special_commercial_charge", "cancellation"]
        )
    )

    # Alias for backward compatibility
    cleaned["is_customer_analysis_ready"] = cleaned["is_commercial_customer_ready"]

    logger.info(
        "Cleaned %d transactions. Standard product sales: %d, Special charges: %d, "
        "Cancellations: %d, Promotional freebies: %d, Commercial customer-ready rows: %d.",
        len(cleaned),
        (cleaned["transaction_category"] == "standard_product_sale").sum(),
        (cleaned["transaction_category"] == "special_commercial_charge").sum(),
        (cleaned["transaction_category"] == "cancellation").sum(),
        (cleaned["transaction_category"] == "promotional_freebie").sum(),
        cleaned["is_commercial_customer_ready"].sum(),
    )

    return cleaned
