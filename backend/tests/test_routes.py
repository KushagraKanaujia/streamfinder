import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_recommendations_invalid_category():
    response = client.post("/api/recommendations", json={
        "category": "invalid",
        "searchQuery": "test",
        "region": "US"
    })
    assert response.status_code == 400

def test_recommendations_empty_query():
    response = client.post("/api/recommendations", json={
        "category": "movies",
        "searchQuery": "",
        "region": "US"
    })
    assert response.status_code == 422


def test_health_reports_demo_mode():
    response = client.get("/api/health")
    assert "demo_mode" in response.json()


def test_recommendations_return_results():
    # With no API keys configured this exercises the bundled sample data.
    for category in ["movies", "tv", "youtube", "tiktok"]:
        response = client.post("/api/recommendations", json={
            "category": category,
            "searchQuery": "inception",
            "region": "US",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["count"] > 0
        assert all(r["url"].startswith("https://") for r in body["results"])
