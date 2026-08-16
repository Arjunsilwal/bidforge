"""
Unit tests for Estimate Exporter Service (CSV & Excel generation).
"""

from api.models import EstimateModel, LineItemModel
from api.services.exporter import EstimateExporterService


def test_estimate_exporter():
    exporter = EstimateExporterService()
    estimate = EstimateModel(
        id="EST-TEST",
        project_name="Bridge Repair Demo",
        location_region="District 1",
        status="ready",
    )
    line_items = [
        LineItemModel(
            id="EST-TEST-001",
            estimate_id="EST-TEST",
            item_code="02010",
            item_description="Mobilization",
            unit_of_measure="LS",
            quantity=1.0,
            unit_price_low=40000.0,
            unit_price_expected=45000.0,
            unit_price_high=50000.0,
            extended_cost=45000.0,
            matched_spec_section="SECTION 00210",
            justification_text="Historical mean grounded",
        )
    ]

    csv_bytes = exporter.to_csv_bytes(estimate, line_items)
    assert len(csv_bytes) > 0
    assert b"02010" in csv_bytes
    assert b"Mobilization" in csv_bytes

    excel_bytes = exporter.to_excel_bytes(estimate, line_items)
    assert len(excel_bytes) > 0
    assert excel_bytes.startswith(b"PK")  # ZIP / XLSX magic bytes
