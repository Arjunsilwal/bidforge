"""
Canonical Line-Item & Bid Package Schemas.
"""

from datetime import date

from pydantic import BaseModel, Field


class CanonicalLineItem(BaseModel):
    """Normalized line item schema used across ingestion, ML, and output layers."""

    item_id: str = Field(..., description="Unique line item identifier in package")
    item_code: str = Field(..., description="Standard pay item or MasterFormat code (e.g. 02010)")
    item_description: str = Field(..., description="Full textual description of scope of work")
    unit_of_measure: str = Field(
        ..., description="Unit of measurement (e.g. LF, SY, CY, TON, EA, LS)"
    )
    quantity: float = Field(..., gt=0, description="Estimated quantity")
    spec_section: str | None = Field(
        None, description="Matching specification division/section reference"
    )
    category: str | None = Field(
        None, description="High-level trade/category (e.g. Earthwork, Paving)"
    )


class HistoricalBidItem(BaseModel):
    """Historical DOT bid tab row for training and grounding retrieval."""

    contract_id: str
    letting_date: date
    region: str
    item_code: str
    item_description: str
    unit_of_measure: str
    quantity: float
    unit_price: float
    bidder_rank: int = Field(1, description="1 for winning/low bidder, >1 for other bidders")
    market_index_value: float | None = Field(
        None, description="FRED PPI index value at letting date"
    )
    adjusted_unit_price: float | None = Field(
        None, description="Price normalized to current baseline dollars"
    )


class BidPackage(BaseModel):
    """Container for an ingested bid package."""

    package_id: str
    project_name: str
    location_region: str
    letting_target_date: date
    line_items: list[CanonicalLineItem]
    spec_chunks: list[str] = Field(default_factory=list)
