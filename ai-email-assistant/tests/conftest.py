"""
Test configuration for pytest.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)
