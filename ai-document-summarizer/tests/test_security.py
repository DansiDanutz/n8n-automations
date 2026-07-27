from pathlib import Path

import pytest

from main import UPLOAD_DIR, required_secret


API_HEADERS = {"X-API-Key": "test-document-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/upload", None),
        ("post", "/summarize/1", None),
        ("post", "/ask/1", {"question": "private?"}),
        ("get", "/documents", None),
        ("get", "/documents/1", None),
        ("delete", "/documents/1", None),
        ("get", "/stats", None),
    ],
)
def test_document_routes_reject_anonymous_requests(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 401


def test_valid_key_allows_document_listing(client):
    response = client.get("/documents", headers=API_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"documents": [], "total": 0}


def test_upload_uses_server_generated_path(client):
    response = client.post(
        "/upload",
        headers=API_HEADERS,
        files={"file": ("../../outside.txt", b"private document", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "outside.txt"
    assert [path.name for path in Path(UPLOAD_DIR).iterdir()] == ["1.txt"]
    assert not (Path(UPLOAD_DIR).parent / "outside.txt").exists()
    duplicate = client.post(
        "/upload",
        headers=API_HEADERS,
        files={"file": ("different.txt", b"private document", "text/plain")},
    )
    assert duplicate.status_code == 409
    assert client.delete("/documents/1", headers=API_HEADERS).status_code == 200
    assert list(Path(UPLOAD_DIR).iterdir()) == []


def test_cors_preflight_allows_configured_origin_without_api_key(client):
    response = client.options(
        "/documents",
        headers={
            "Origin": "https://documents.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://documents.example"


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_DOCUMENT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_DOCUMENT_SECRET"):
        required_secret("MISSING_DOCUMENT_SECRET", 32)


def test_required_secret_rejects_documented_placeholder(monkeypatch):
    monkeypatch.setenv("PLACEHOLDER_DOCUMENT_SECRET", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="PLACEHOLDER_DOCUMENT_SECRET"):
        required_secret("PLACEHOLDER_DOCUMENT_SECRET", 32)
