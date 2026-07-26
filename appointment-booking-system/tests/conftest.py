import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_API_KEY", "test-admin-api-key-that-is-at-least-32-characters")

from main import app, bookings_db, time_slots_db


@pytest.fixture
def client():
    bookings_db.clear()
    time_slots_db.clear()
    with TestClient(app) as test_client:
        yield test_client
    bookings_db.clear()
    time_slots_db.clear()
