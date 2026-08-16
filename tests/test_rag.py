"""
Unit tests for RAG Grounding Service (spec matching & comparable bid lookup).
"""
from datetime import date
from data.schemas import CanonicalLineItem, HistoricalBidItem
from api.services.rag import RAGGroundingService


def test_rag_spec_matching():
    service = RAGGroundingService()
    item = CanonicalLineItem(
        item_id="ITEM-001",
        item_code="02010",
        item_description="Mobilization and Demobilization",
        unit_of_measure="LS",
        quantity=1.0,
    )
    spec_chunks = [
        "SECTION 00330 - EARTHWORK & EXCAVATION\nRoadway cut and fill operations.",
        "SECTION 00210 - MOBILIZATION\nExecution and staging standards for mobilization (Code 02010).",
        "SECTION 00745 - ASPHALT PAVEMENT\nSuperpave level 3 mix designs.",
    ]

    matched_section = service.match_spec_section(item, spec_chunks)
    assert matched_section is not None
    assert "00210 - MOBILIZATION" in matched_section


def test_rag_comparable_bids():
    hist_bids = [
        HistoricalBidItem(
            contract_id="C001",
            letting_date=date(2023, 1, 1),
            region="District 1",
            item_code="02010",
            item_description="Mobilization",
            unit_of_measure="LS",
            quantity=1.0,
            unit_price=45000.0,
        ),
        HistoricalBidItem(
            contract_id="C002",
            letting_date=date(2023, 2, 1),
            region="District 1",
            item_code="02010",
            item_description="Mobilization",
            unit_of_measure="LS",
            quantity=1.0,
            unit_price=48000.0,
        ),
        HistoricalBidItem(
            contract_id="C003",
            letting_date=date(2023, 3, 1),
            region="District 2",
            item_code="03010",
            item_description="Aggregate Base",
            unit_of_measure="TON",
            quantity=1000.0,
            unit_price=30.0,
        ),
    ]

    service = RAGGroundingService(historical_bids=hist_bids)
    item = CanonicalLineItem(
        item_id="ITEM-001",
        item_code="02010",
        item_description="Mobilization",
        unit_of_measure="LS",
        quantity=1.0,
    )

    comps = service.find_comparable_bids(item, top_k=2)
    assert len(comps) == 2
    assert comps[0].contract_id in ["C001", "C002"]
