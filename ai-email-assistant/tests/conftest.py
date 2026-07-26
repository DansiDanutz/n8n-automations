"""
Test configuration for pytest.
"""
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-that-is-at-least-32-characters")
os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret-at-least-32-characters")
from backend.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)
