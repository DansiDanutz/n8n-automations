"""
Tests for ai-seo-content-generator API
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_not_found():
    """Test 404 handling."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
