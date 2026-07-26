import pytest

from main import bookings_db, required_secret, time_slots_db


ADMIN_HEADERS = {"X-API-Key": "test-admin-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/bookings", None),
        ("post", "/slots", {"date": "2030-01-01", "start_time": "09:00", "end_time": "10:00"}),
        ("delete", "/bookings/BOOKING1", None),
        ("put", "/bookings/BOOKING1", {}),
        ("get", "/stats", None),
    ],
)
def test_administrative_routes_reject_missing_key(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 401


def test_admin_key_allows_booking_list(client):
    response = client.get("/bookings", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_public_availability_does_not_disclose_booking_identity(client):
    time_slots_db["2030-01-01_09:00"] = {
        "date": "2030-01-01",
        "start_time": "09:00",
        "end_time": "10:00",
        "duration": 60,
        "service_types": ["consultation"],
    }
    bookings_db["PRIVATE1"] = {
        "id": "PRIVATE1",
        "client_name": "Private Client",
        "client_email": "private@example.com",
        "client_phone": "+1-555-0100",
        "service_type": "consultation",
        "date": "2030-01-01",
        "time": "09:00",
        "duration": 60,
        "notes": "private note",
        "status": "confirmed",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }

    response = client.get("/availability", params={"date": "2030-01-01"})
    assert response.status_code == 200
    body = response.text
    assert "Private Client" not in body
    assert "PRIVATE1" not in body
    assert "private@example.com" not in body
    assert response.json()["booked_slots"] == [
        {
            "time": "09:00",
            "duration": 60,
            "service_types": ["consultation"],
            "end_time": "10:00",
            "status": "unavailable",
        }
    ]


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_APPOINTMENT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_APPOINTMENT_SECRET"):
        required_secret("MISSING_APPOINTMENT_SECRET", 32)
