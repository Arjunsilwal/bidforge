"""
State DOT Bid Tabulation Parser & Canonicalizer.
Parses public letting spreadsheets/CSV files (e.g. Oregon DOT) into canonical structures.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Union
import pandas as pd
from data.schemas import HistoricalBidItem


class DOTBidTabParser:
    """Parser for State Department of Transportation bid tabulation data."""

    # Standard column mappings across state variations
    COLUMN_ALIASES = {
        "item_code": ["item_code", "item_no", "item_num", "pay_item", "item_number"],
        "item_description": ["item_description", "description", "item_desc", "item_name"],
        "unit_of_measure": ["unit_of_measure", "unit", "uom", "meas_unit"],
        "quantity": ["quantity", "est_qty", "plan_qty", "qty"],
        "unit_price": ["unit_price", "bid_price", "unit_bid", "price"],
        "letting_date": ["letting_date", "bid_date", "let_date", "date"],
        "region": ["region", "district", "county", "location"],
        "contract_id": ["contract_id", "project_no", "contract_no", "call_no"],
        "bidder_rank": ["bidder_rank", "rank", "bidder_pos"],
    }

    def __init__(self, target_state: str = "OR"):
        self.target_state = target_state

    def parse_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Read CSV or Excel DOT bid tabulation and standardize column names."""
        path = Path(file_path)
        if path.suffix.lower() in [".xls", ".xlsx"]:
            df = pd.read_excel(path)
        elif path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        standardized_df = self._standardize_columns(df)
        clean_df = self._clean_data(standardized_df)
        return clean_df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map raw column headers to canonical names."""
        df_cols_lower = {str(c).strip().lower(): c for c in df.columns}
        rename_map = {}

        for canonical_name, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in df_cols_lower:
                    rename_map[df_cols_lower[alias]] = canonical_name
                    break

        df = df.rename(columns=rename_map)
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data types, remove invalid quantities/prices, and parse dates."""
        df = df.copy()

        # Clean numerical fields
        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        if "unit_price" in df.columns:
            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        if "bidder_rank" in df.columns:
            df["bidder_rank"] = pd.to_numeric(df["bidder_rank"], errors="coerce").fillna(1).astype(int)
        else:
            df["bidder_rank"] = 1

        # Clean string fields
        if "item_code" in df.columns:
            df["item_code"] = df["item_code"].astype(str).str.strip()
        if "item_description" in df.columns:
            df["item_description"] = df["item_description"].astype(str).str.strip()
        if "unit_of_measure" in df.columns:
            df["unit_of_measure"] = df["unit_of_measure"].astype(str).str.upper().str.strip()
        if "region" in df.columns:
            df["region"] = df["region"].astype(str).str.strip()
        else:
            df["region"] = "Default Region"
        if "contract_id" in df.columns:
            df["contract_id"] = df["contract_id"].astype(str).str.strip()

        # Clean date fields
        if "letting_date" in df.columns:
            df["letting_date"] = pd.to_datetime(df["letting_date"], errors="coerce").dt.date

        # Drop invalid pricing and zero/negative quantities
        df = df.dropna(subset=["quantity", "unit_price", "item_code"])
        df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
        return df

    def to_historical_items(self, df: pd.DataFrame) -> List[HistoricalBidItem]:
        """Convert cleaned DataFrame to list of Pydantic HistoricalBidItem models."""
        items = []
        for _, row in df.iterrows():
            items.append(
                HistoricalBidItem(
                    contract_id=str(row.get("contract_id", "UNKNOWN")),
                    letting_date=row["letting_date"],
                    region=str(row.get("region", "UNKNOWN")),
                    item_code=str(row["item_code"]),
                    item_description=str(row["item_description"]),
                    unit_of_measure=str(row["unit_of_measure"]),
                    quantity=float(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    bidder_rank=int(row.get("bidder_rank", 1)),
                )
            )
        return items
