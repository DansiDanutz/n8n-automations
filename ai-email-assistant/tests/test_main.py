"""
Tests for ai-email-assistant API
"""
def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_not_found(client):
    """Test 404 handling."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_webhook_rejects_missing_secret(client):
    response = client.post(
        "/webhooks/email-received",
        json={"event": "email.received", "timestamp": "2026-01-01T00:00:00Z", "data": {"user_id": "user", "email_id": "email"}},
    )
    assert response.status_code == 401


def test_bulk_webhook_rejects_invalid_limit(client):
    response = client.post(
        "/webhooks/bulk-process",
        headers={"X-Webhook-Secret": "test-webhook-secret-at-least-32-characters"},
        json={"event": "bulk.process", "timestamp": "2026-01-01T00:00:00Z", "data": {"user_id": "user", "limit": 1000}},
    )
    assert response.status_code == 422


def test_required_secret_fails_closed(monkeypatch):
    from backend.services.auth_service import required_secret

    monkeypatch.delenv("UNSET_TEST_SECRET", raising=False)
    try:
        required_secret("UNSET_TEST_SECRET", 32)
    except RuntimeError as error:
        assert "UNSET_TEST_SECRET" in str(error)
    else:
        raise AssertionError("missing secret was accepted")
