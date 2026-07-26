import pytest

from main import required_secret


API_HEADERS = {"X-API-Key": "test-social-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/posts", {"content": "Do not publish", "platforms": ["twitter"]}),
        ("get", "/posts", None),
        ("get", "/posts/private", None),
        ("post", "/posts/private/publish", None),
        ("delete", "/posts/private", None),
        ("get", "/analytics", None),
        ("get", "/platforms", None),
    ],
)
def test_control_plane_rejects_anonymous_requests(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 401


def test_valid_key_allows_post_listing(client):
    response = client.get("/posts", headers=API_HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_public_health_does_not_expose_platform_configuration(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "configured_platforms" not in response.json()
    assert "scheduler_running" not in response.json()


def test_cors_preflight_allows_configured_origin_without_api_key(client):
    response = client.options(
        "/posts",
        headers={
            "Origin": "https://console.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://console.example"


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_SOCIAL_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_SOCIAL_SECRET"):
        required_secret("MISSING_SOCIAL_SECRET", 32)


def test_required_secret_rejects_documented_placeholder(monkeypatch):
    monkeypatch.setenv("PLACEHOLDER_SOCIAL_SECRET", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="PLACEHOLDER_SOCIAL_SECRET"):
        required_secret("PLACEHOLDER_SOCIAL_SECRET", 32)
