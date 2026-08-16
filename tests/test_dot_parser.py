"""
Unit tests for DOT Bid Tabulation Parser.
"""

from datetime import date

import pandas as pd

from data.dot_parser import DOTBidTabParser


def test_dot_parser_standardize_and_clean():
    parser = DOTBidTabParser()
    raw_df = pd.DataFrame(
        {
            "Item_No": ["02010", "02020", "INVALID"],
            "Item_Desc": ["Mobilization", "Clearing", "Bad Row"],
            "Meas_Unit": ["LS", "ACRE", "LS"],
            "Est_Qty": [1.0, 5.5, -2.0],  # Negative qty should be filtered out
            "Unit_Bid": ["1000.50", "250.00", "0.00"],  # Zero price should be filtered out
            "Let_Date": ["2023-05-12", "2023-06-15", "invalid-date"],
            "District": ["District 1", "District 2", "District 1"],
        }
    )

    cleaned = parser._clean_data(parser._standardize_columns(raw_df))

    # Should retain the 2 valid rows and drop the invalid row
    assert len(cleaned) == 2
    assert "item_code" in cleaned.columns
    assert "unit_price" in cleaned.columns
    assert cleaned.iloc[0]["quantity"] == 1.0
    assert cleaned.iloc[0]["unit_price"] == 1000.50
    assert cleaned.iloc[0]["letting_date"] == date(2023, 5, 12)


def test_to_historical_items():
    parser = DOTBidTabParser()
    df = pd.DataFrame(
        {
            "contract_id": ["C1001"],
            "letting_date": [date(2023, 4, 1)],
            "region": ["District 1"],
            "item_code": ["02010"],
            "item_description": ["Mobilization"],
            "unit_of_measure": ["LS"],
            "quantity": [1.0],
            "unit_price": [5000.0],
            "bidder_rank": [1],
        }
    )
    items = parser.to_historical_items(df)
    assert len(items) == 1
    assert items[0].contract_id == "C1001"
    assert items[0].unit_price == 5000.0
