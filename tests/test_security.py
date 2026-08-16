"""
Regression tests for the security hardening: CSV/Excel formula injection, upload size
limits, input bounds, and CORS configuration.
"""

import io

from fastapi.testclient import TestClient

from api.main import app
from api.models import EstimateModel, LineItemModel
from api.routes.estimates import MAX_UPLOAD_BYTES
from api.services.exporter import EstimateExporterService

client = TestClient(app)


def _line_item(description: str, item_id: str = "EST-SEC-001") -> LineItemModel:
    return LineItemModel(
        id=item_id,
        estimate_id="EST-SEC",
        item_code="02010",
        item_description=description,
        unit_of_measure="LS",
        quantity=1.0,
        unit_price_low=1.0,
        unit_price_expected=2.0,
        unit_price_high=3.0,
        extended_cost=2.0,
    )


def test_export_neutralizes_formula_injection():
    """A malicious BOQ description must not export as a live spreadsheet formula."""
    exporter = EstimateExporterService()
    estimate = EstimateModel(id="EST-SEC", project_name="P", location_region="R", status="ready")

    payload = '=cmd|" /C calc"!A0'
    csv_bytes = exporter.to_csv_bytes(estimate, [_line_item(payload)])
    csv_text = csv_bytes.decode("utf-8")

    # The cell is quoted and prefixed, so a spreadsheet treats it as text.
    assert "'=cmd" in csv_text
    # No cell begins a formula directly after a delimiter or quote.
    assert ",=cmd" not in csv_text
    assert '"=cmd' not in csv_text


def test_export_prefixes_every_risky_leading_character():
    exporter = EstimateExporterService()
    estimate = EstimateModel(id="EST-SEC", project_name="P", location_region="R", status="ready")

    for prefix in ("=", "+", "-", "@"):
        df = exporter.to_dataframe(estimate, [_line_item(f"{prefix}HYPERLINK(0)")])
        assert df.iloc[0]["Description"].startswith("'"), f"{prefix!r} was not neutralized"


def test_export_leaves_benign_text_untouched():
    exporter = EstimateExporterService()
    estimate = EstimateModel(id="EST-SEC", project_name="P", location_region="R", status="ready")

    df = exporter.to_dataframe(estimate, [_line_item("Mobilization and Demobilization")])
    assert df.iloc[0]["Description"] == "Mobilization and Demobilization"


def test_upload_rejects_oversized_file():
    """Files over the cap are refused with 413 rather than buffered and parsed."""
    oversized = b"x" * (MAX_UPLOAD_BYTES + 1024)
    response = client.post(
        "/api/v1/estimates/upload",
        data={"project_name": "Too Big"},
        files={"boq_file": ("big.csv", io.BytesIO(oversized), "text/csv")},
    )
    assert response.status_code == 413


def test_upload_rejects_unsupported_extension():
    response = client.post(
        "/api/v1/estimates/upload",
        data={"project_name": "Bad Type"},
        files={"boq_file": ("payload.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_does_not_leak_parser_internals():
    """A malformed-but-supported file returns a generic message, not a stack trace."""
    response = client.post(
        "/api/v1/estimates/upload",
        data={"project_name": "Corrupt"},
        files={
            "boq_file": ("boq.xlsx", io.BytesIO(b"not really xlsx"), "application/vnd.ms-excel")
        },
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    for leak in ("Traceback", "openpyxl", "pandas", "/app/", 'File "'):
        assert leak not in detail


def test_synthetic_rejects_out_of_range_item_count():
    """item_count is bounded; unbounded values previously reached random.sample."""
    assert client.post("/api/v1/estimates/synthetic", params={"item_count": 0}).status_code == 422
    assert client.post("/api/v1/estimates/synthetic", params={"item_count": -5}).status_code == 422
    assert client.post("/api/v1/estimates/synthetic", params={"item_count": 999}).status_code == 422


def test_override_rejects_non_finite_and_out_of_range_prices():
    created = client.post("/api/v1/estimates/synthetic", params={"item_count": 2})
    assert created.status_code == 200
    estimate = created.json()
    item_id = estimate["line_items"][0]["id"]
    url = f"/api/v1/estimates/{estimate['id']}/line-items/{item_id}"

    # Non-finite values must not reach the totals or the export.
    assert client.patch(url, content='{"overridden_unit_price": Infinity}').status_code == 422
    assert client.patch(url, content='{"overridden_unit_price": NaN}').status_code == 422
    # Bounds still apply.
    assert client.patch(url, json={"overridden_unit_price": 0}).status_code == 422
    assert client.patch(url, json={"overridden_unit_price": -1}).status_code == 422
    assert client.patch(url, json={"overridden_unit_price": 1e12}).status_code == 422
    # A sane price is still accepted.
    assert client.patch(url, json={"overridden_unit_price": 123.45}).status_code == 200


def test_cors_never_falls_back_to_wildcard():
    """An empty allowlist must mean 'no cross-origin access', not '*'."""
    from api.config import Settings

    settings = Settings(ALLOWED_ORIGINS="")
    assert settings.cors_origins == []

    settings = Settings(ALLOWED_ORIGINS="https://app.example.com, https://admin.example.com")
    assert settings.cors_origins == ["https://app.example.com", "https://admin.example.com"]
