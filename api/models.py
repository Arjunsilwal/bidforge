"""
SQLAlchemy ORM Models for Estimates, Line Items, Historical Bids, and Spec Chunks.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from api.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class EstimateModel(Base):
    """Represents a full bid package estimate project."""
    __tablename__ = "estimates"

    id = Column(String(64), primary_key=True, index=True)
    project_name = Column(String(255), nullable=False)
    location_region = Column(String(100), default="Default Region")
    status = Column(String(50), default="draft")  # draft, processing, ready, approved
    total_cost_low = Column(Float, default=0.0)
    total_cost_expected = Column(Float, default=0.0)
    total_cost_high = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    line_items = relationship("LineItemModel", back_populates="estimate", cascade="all, delete-orphan")
    spec_chunks = relationship("SpecChunkModel", back_populates="estimate", cascade="all, delete-orphan")


class LineItemModel(Base):
    """Represents a single estimated line item."""
    __tablename__ = "line_items"

    id = Column(String(64), primary_key=True, index=True)
    estimate_id = Column(String(64), ForeignKey("estimates.id"), nullable=False, index=True)
    item_code = Column(String(50), nullable=False, index=True)
    item_description = Column(Text, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)

    # Predictions
    unit_price_low = Column(Float, default=0.0)
    unit_price_expected = Column(Float, default=0.0)
    unit_price_high = Column(Float, default=0.0)
    extended_cost = Column(Float, default=0.0)

    # User overrides
    is_overridden = Column(Boolean, default=False)
    overridden_unit_price = Column(Float, nullable=True)

    # Traceability & Justification
    matched_spec_section = Column(String(255), nullable=True)
    justification_text = Column(Text, nullable=True)
    comparable_bids = Column(JSON, default=list)

    estimate = relationship("EstimateModel", back_populates="line_items")


class SpecChunkModel(Base):
    """Represents a parsed text section from the project spec PDF."""
    __tablename__ = "spec_chunks"

    id = Column(String(64), primary_key=True, index=True)
    estimate_id = Column(String(64), ForeignKey("estimates.id"), nullable=False, index=True)
    section_title = Column(String(255), nullable=True)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    estimate = relationship("EstimateModel", back_populates="spec_chunks")
