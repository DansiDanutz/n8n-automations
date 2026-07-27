import os
import tempfile

import pytest
from fastapi.testclient import TestClient

test_root = tempfile.mkdtemp(prefix="support-bot-test-")
os.environ.setdefault("API_KEY", "test-support-api-key-that-is-at-least-32-characters")
os.environ["DB_PATH"] = os.path.join(test_root, "support.db")
os.environ["KB_DIR"] = os.path.join(test_root, "knowledge")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://support.example")

from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
