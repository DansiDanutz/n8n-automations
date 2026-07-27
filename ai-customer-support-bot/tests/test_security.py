import pytest

from main import required_secret


API_HEADERS = {"X-API-Key": "test-support-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/chat", {"message": "private", "user_id": "user-a"}),
        ("get", "/conversations", None),
        ("get", "/conversations/1", None),
        ("post", "/feedback", {"conversation_id": 1, "rating": 5}),
        ("get", "/analytics", None),
    ],
)
def test_support_routes_reject_anonymous_requests(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 401


def test_authenticated_chat_continues_only_for_matching_user(client):
    first = client.post(
        "/chat",
        headers=API_HEADERS,
        json={"message": "First private question", "user_id": "user-a"},
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    continued = client.post(
        "/chat",
        headers=API_HEADERS,
        json={"message": "Continue", "user_id": "user-a", "conversation_id": conversation_id},
    )
    assert continued.status_code == 200
    assert continued.json()["conversation_id"] == conversation_id

    mismatched = client.post(
        "/chat",
        headers=API_HEADERS,
        json={"message": "Attempt reuse", "user_id": "user-b", "conversation_id": conversation_id},
    )
    assert mismatched.status_code == 200
    assert mismatched.json()["conversation_id"] != conversation_id

    detail = client.get(f"/conversations/{conversation_id}", headers=API_HEADERS)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 4


def test_cors_preflight_allows_configured_origin_without_api_key(client):
    response = client.options(
        "/chat",
        headers={
            "Origin": "https://support.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://support.example"


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_SUPPORT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_SUPPORT_SECRET"):
        required_secret("MISSING_SUPPORT_SECRET", 32)


def test_required_secret_rejects_documented_placeholder(monkeypatch):
    monkeypatch.setenv("PLACEHOLDER_SUPPORT_SECRET", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="PLACEHOLDER_SUPPORT_SECRET"):
        required_secret("PLACEHOLDER_SUPPORT_SECRET", 32)
