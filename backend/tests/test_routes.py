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
