import os
import tempfile

import pytest
from fastapi.testclient import TestClient

test_root = tempfile.mkdtemp(prefix="document-api-test-")
os.environ.setdefault("API_KEY", "test-document-api-key-that-is-at-least-32-characters")
os.environ["DB_PATH"] = os.path.join(test_root, "documents.db")
os.environ["UPLOAD_DIR"] = os.path.join(test_root, "uploads")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://documents.example")

from main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
