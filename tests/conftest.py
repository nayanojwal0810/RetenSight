"""Synthetic fixtures for unit testing RetenSight pipeline components."""

from datetime import datetime
import pandas as pd
import pytest


@pytest.fixture
def synthetic_sheets():
    """Generates synthetic Sheet 1 and Sheet 2 with known overlap and edge cases.

    Scenarios included:
    1. Exact cross-sheet duplicate row (1-to-1 match across sheets).
    2. Multiplicity cross-sheet duplicate:
       - Row A appears 2 times in Sheet 1, 1 time in Sheet 2 -> 1 removed from Sheet 2.
       - Row B appears 1 time in Sheet 1, 2 times in Sheet 2 -> 1 removed from Sheet 2, 1 retained in Sheet 2.
    3. Legitimate same-sheet duplicates:
       - Row C appears 2 times in Sheet 1, 0 times in Sheet 2 -> both preserved in Sheet 1.
    4. Cancellation invoice ('C10001', negative quantity, positive price).
    5. Zero-price inventory write-off (Quantity < 0, Price == 0, Customer ID NaN).
    6. Zero-price promotional gift (Quantity > 0, Price == 0, Customer ID populated).
    7. Bad debt adjustment ('A10002', StockCode 'B', Price < 0, Customer ID NaN).
    8. Null Customer ID with positive sales.
    """
    cols = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    ]

    # Sheet 1 records
    s1_rows = [
        # Normal sales
        ("500001", "85048", "Product 1", 2, datetime(2010, 1, 10, 10, 0), 5.0, 12345, "United Kingdom"),
        # Cross-sheet duplicate candidate (Row X)
        ("500002", "85049", "Product 2", 1, datetime(2010, 12, 5, 12, 0), 10.0, 12345, "United Kingdom"),
        # Multiplicity candidate A (appears 2 times in S1, 1 time in S2)
        ("500003", "85050", "Product A", 3, datetime(2010, 12, 6, 14, 0), 4.0, 12346, "United Kingdom"),
        ("500003", "85050", "Product A", 3, datetime(2010, 12, 6, 14, 0), 4.0, 12346, "United Kingdom"),
        # Multiplicity candidate B (appears 1 time in S1, 2 times in S2)
        ("500004", "85051", "Product B", 2, datetime(2010, 12, 7, 15, 0), 6.0, 12347, "United Kingdom"),
        # Same-sheet duplicate in S1 (appears 2 times in S1, 0 in S2)
        ("500005", "85052", "Product C", 4, datetime(2010, 2, 1, 9, 30), 2.5, 12348, "United Kingdom"),
        ("500005", "85052", "Product C", 4, datetime(2010, 2, 1, 9, 30), 2.5, 12348, "United Kingdom"),
        # Cancellation
        ("C500006", "85048", "Product 1", -1, datetime(2010, 3, 1, 11, 0), 5.0, 12345, "United Kingdom"),
        # Zero price inventory adjustment (NaN customer)
        ("500007", "85053", "damages", -10, datetime(2010, 4, 1, 12, 0), 0.0, None, "United Kingdom"),
        # Zero price promotional freebie (valid customer)
        ("500008", "85054", "Free gift", 1, datetime(2010, 5, 1, 13, 0), 0.0, 12349, "United Kingdom"),
        # Bad debt adjustment ('A')
        ("A500009", "B", "Adjust bad debt", 1, datetime(2010, 6, 1, 14, 0), -100.0, None, "United Kingdom"),
        # Unattributed sale (missing customer)
        ("500010", "85055", "Product Unattr", 5, datetime(2010, 7, 1, 15, 0), 2.0, None, "United Kingdom"),
    ]

    # Sheet 2 records
    s2_rows = [
        # Exactly identical to Row X in S1 -> MUST BE DROPPED
        ("500002", "85049", "Product 2", 1, datetime(2010, 12, 5, 12, 0), 10.0, 12345, "United Kingdom"),
        # Multiplicity candidate A (appears 1 time in S2) -> MUST BE DROPPED
        ("500003", "85050", "Product A", 3, datetime(2010, 12, 6, 14, 0), 4.0, 12346, "United Kingdom"),
        # Multiplicity candidate B (appears 2 times in S2) -> 1 DROPPED, 1 KEPT
        ("500004", "85051", "Product B", 2, datetime(2010, 12, 7, 15, 0), 6.0, 12347, "United Kingdom"),
        ("500004", "85051", "Product B", 2, datetime(2010, 12, 7, 15, 0), 6.0, 12347, "United Kingdom"),
        # New 2011 sale
        ("500011", "85056", "Product 2011", 10, datetime(2011, 1, 15, 10, 0), 3.0, 12350, "United Kingdom"),
    ]

    df1 = pd.DataFrame(s1_rows, columns=cols)
    df1["source_sheet"] = "Year 2009-2010"
    df1["source_row_num"] = df1.index + 2

    df2 = pd.DataFrame(s2_rows, columns=cols)
    df2["source_sheet"] = "Year 2010-2011"
    df2["source_row_num"] = df2.index + 2

    return df1, df2
