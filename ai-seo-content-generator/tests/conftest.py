import os

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("API_KEY", "test-seo-api-key-that-is-at-least-32-characters")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://seo.example")

from main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
