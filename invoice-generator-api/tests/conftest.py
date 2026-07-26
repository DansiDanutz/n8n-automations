import os
import tempfile

import pytest
from fastapi.testclient import TestClient

database_handle, database_path = tempfile.mkstemp(prefix="invoice-api-test-", suffix=".db")
os.close(database_handle)
os.unlink(database_path)
os.environ.setdefault("API_KEY", "test-invoice-api-key-that-is-at-least-32-characters")
os.environ["DB_PATH"] = database_path
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://billing.example")

from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
    if os.path.exists(database_path):
        os.unlink(database_path)
