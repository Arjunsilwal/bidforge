"""
Pydantic API Request and Response Schemas.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ComparableBidSchema(BaseModel):
    """Comparable historical bid item summary."""
    contract_id: str
    letting_date: str
    region: str
    unit_price: float
    quantity: float
    adjusted_price: float


class LineItemResponse(BaseModel):
    id: str
    item_code: str
    item_description: str
    unit_of_measure: str
    quantity: float
    unit_price_low: float
    unit_price_expected: float
    unit_price_high: float
    extended_cost: float
    is_overridden: bool = False
    overridden_unit_price: Optional[float] = None
    matched_spec_section: Optional[str] = None
    justification_text: Optional[str] = None
    comparable_bids: List[ComparableBidSchema] = Field(default_factory=list)


class LineItemOverrideRequest(BaseModel):
    overridden_unit_price: float = Field(..., gt=0, description="New manual unit price to assign to the line item")


class EstimateSummaryResponse(BaseModel):
    id: str
    project_name: str
    location_region: str
    status: str
    total_cost_low: float
    total_cost_expected: float
    total_cost_high: float
    line_item_count: int
    created_at: datetime
    updated_at: datetime


class EstimateDetailResponse(EstimateSummaryResponse):
    line_items: List[LineItemResponse]


class EstimateCreateRequest(BaseModel):
    project_name: str
    location_region: str = "Default Region"
