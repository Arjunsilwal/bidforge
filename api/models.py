"""
SQLAlchemy ORM Models for Estimates, Line Items, Historical Bids, and Spec Chunks.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class EstimateModel(Base):
    """Represents a full bid package estimate project."""

    __tablename__ = "estimates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_region: Mapped[str] = mapped_column(String(100), default="Default Region")
    # draft, processing, ready, approved
    status: Mapped[str] = mapped_column(String(50), default="draft")
    total_cost_low: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_expected: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_high: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    line_items: Mapped[list["LineItemModel"]] = relationship(
        back_populates="estimate", cascade="all, delete-orphan"
    )
    spec_chunks: Mapped[list["SpecChunkModel"]] = relationship(
        back_populates="estimate", cascade="all, delete-orphan"
    )


class LineItemModel(Base):
    """Represents a single estimated line item."""

    __tablename__ = "line_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    estimate_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("estimates.id"), nullable=False, index=True
    )
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Predictions
    unit_price_low: Mapped[float] = mapped_column(Float, default=0.0)
    unit_price_expected: Mapped[float] = mapped_column(Float, default=0.0)
    unit_price_high: Mapped[float] = mapped_column(Float, default=0.0)
    extended_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # User overrides
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    overridden_unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Traceability & Justification
    matched_spec_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    justification_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparable_bids: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    estimate: Mapped["EstimateModel"] = relationship(back_populates="line_items")

    @property
    def effective_unit_price(self) -> float:
        """Unit price actually used for costing: the manual override when one is set,
        otherwise the model's expected (50th percentile) prediction."""
        if self.is_overridden and self.overridden_unit_price is not None:
            return self.overridden_unit_price
        return self.unit_price_expected


class SpecChunkModel(Base):
    """Represents a parsed text section from the project spec PDF."""

    __tablename__ = "spec_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    estimate_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("estimates.id"), nullable=False, index=True
    )
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    estimate: Mapped["EstimateModel"] = relationship(back_populates="spec_chunks")
