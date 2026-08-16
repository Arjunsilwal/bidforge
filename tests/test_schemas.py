"""
Tests for canonical data schemas and synthetic generator.
"""
from datetime import date
import pytest
from data.schemas import CanonicalLineItem, BidPackage
from data.synthetic_generator import SyntheticBidPackageGenerator


def test_canonical_line_item():
    item = CanonicalLineItem(
        item_id="ITEM-001",
        item_code="02010",
        item_description="Mobilization and Demobilization",
        unit_of_measure="LS",
        quantity=1.0,
    )
    assert item.item_code == "02010"
    assert item.quantity == 1.0


def test_synthetic_package_generation():
    gen = SyntheticBidPackageGenerator()
    pkg = gen.generate_bid_package(item_count=5)
    assert len(pkg.line_items) == 5
    assert len(pkg.spec_chunks) == 5
    assert pkg.package_id.startswith("PKG-")
