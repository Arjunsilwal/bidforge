"""
Tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient

from api.main import app

# Tables are created by the session-scoped `_create_schema` fixture in conftest.py.
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "BidForge"


def test_synthetic_estimate_endpoint():
    response = client.post("/api/v1/estimates/synthetic", params={"item_count": 3})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "ready"
    assert len(data["line_items"]) == 3
    assert data["total_cost_expected"] > 0
